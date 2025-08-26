"""
Intelligent Summarization Service for Memory-Server
Advanced document and content summarization with LLM integration
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import json
import hashlib
from datetime import datetime

from core.config import get_config
from core.logging_config import get_logger
from .content_analyzer import ContentAnalyzer

logger = get_logger("summarization-service")
config = get_config()

class SummaryType(str, Enum):
    EXTRACTIVE = "extractive"  # Extract key sentences
    ABSTRACTIVE = "abstractive"  # Generate new summary text
    STRUCTURED = "structured"  # Structured summary with sections
    BULLET_POINTS = "bullet_points"  # Key points format
    TECHNICAL = "technical"  # Technical documentation style
    NARRATIVE = "narrative"  # Story-like summary

class SummaryLength(str, Enum):
    SHORT = "short"  # 1-2 sentences
    MEDIUM = "medium"  # 1-2 paragraphs  
    LONG = "long"  # Multiple paragraphs
    COMPREHENSIVE = "comprehensive"  # Detailed analysis

@dataclass
class SummaryRequest:
    content: str
    title: Optional[str] = None
    content_type: Optional[str] = None
    workspace: str = "research"
    summary_type: SummaryType = SummaryType.ABSTRACTIVE
    length: SummaryLength = SummaryLength.MEDIUM
    language: str = "en"
    include_keywords: bool = True
    include_entities: bool = True
    custom_prompt: Optional[str] = None

@dataclass 
class SummaryResponse:
    summary: str
    summary_type: str
    length: str
    keywords: List[str]
    entities: List[str]
    confidence_score: float
    processing_time: float
    metadata: Dict[str, Any]

class SummarizationService:
    """Advanced summarization service with LLM integration"""
    
    def __init__(self):
        self.llm_server_url = os.getenv("LLM_SERVER_URL", "http://localhost:8000")
        self.content_analyzer = ContentAnalyzer()
        
        # Summary templates for different types
        self.templates = {
            SummaryType.EXTRACTIVE: self._get_extractive_template(),
            SummaryType.ABSTRACTIVE: self._get_abstractive_template(),
            SummaryType.STRUCTURED: self._get_structured_template(),
            SummaryType.BULLET_POINTS: self._get_bullet_points_template(),
            SummaryType.TECHNICAL: self._get_technical_template(),
            SummaryType.NARRATIVE: self._get_narrative_template()
        }
        
        # Cache for avoiding duplicate summarizations
        self.cache = {}
    
    async def summarize(self, request: SummaryRequest) -> SummaryResponse:
        """Generate intelligent summary based on request parameters"""
        start_time = datetime.now()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(request)
            if cache_key in self.cache:
                logger.info(f"Using cached summary for content")
                cached = self.cache[cache_key]
                cached.processing_time = (datetime.now() - start_time).total_seconds()
                return cached
            
            # Analyze content first
            content_analysis = await self.content_analyzer.analyze_content(
                content=request.content,
                filename=request.title or "document",
                workspace=request.workspace
            )
            
            # Determine optimal summary approach
            optimal_type = self._determine_optimal_summary_type(
                request, content_analysis
            )
            
            # Generate summary using LLM
            summary_text = await self._generate_llm_summary(
                request, content_analysis, optimal_type
            )
            
            # Extract keywords and entities
            keywords = self._extract_keywords(request.content, content_analysis)
            entities = self._extract_entities(request.content, content_analysis)
            
            # Calculate confidence score
            confidence = self._calculate_confidence_score(
                request.content, summary_text, content_analysis
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create response
            response = SummaryResponse(
                summary=summary_text,
                summary_type=optimal_type.value,
                length=request.length.value,
                keywords=keywords,
                entities=entities,
                confidence_score=confidence,
                processing_time=processing_time,
                metadata={
                    "content_length": len(request.content),
                    "content_type": content_analysis.get("content_type", "unknown"),
                    "language": content_analysis.get("language", request.language),
                    "is_code": content_analysis.get("is_code", False),
                    "frameworks": content_analysis.get("frameworks", []),
                    "complexity_score": content_analysis.get("complexity_score", 0.0),
                    "template_used": optimal_type.value,
                    "llm_model": content_analysis.get("suggested_model", "default")
                }
            )
            
            # Cache the result
            self.cache[cache_key] = response
            
            logger.info(f"Generated {optimal_type.value} summary in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            # Fallback to simple extractive summary
            return await self._fallback_summary(request, start_time)
    
    async def summarize_document(
        self, 
        document_content: str, 
        document_metadata: Dict[str, Any]
    ) -> SummaryResponse:
        """Summarize a document with its metadata context"""
        
        # Create request from document data
        request = SummaryRequest(
            content=document_content,
            title=document_metadata.get("original_filename", "Document"),
            content_type=document_metadata.get("content_type", "document"),
            workspace=document_metadata.get("workspace", "research"),
            summary_type=self._suggest_summary_type_from_metadata(document_metadata),
            length=self._suggest_length_from_content(document_content),
            include_keywords=True,
            include_entities=True
        )
        
        return await self.summarize(request)
    
    async def batch_summarize(
        self, 
        requests: List[SummaryRequest],
        max_concurrent: int = 5
    ) -> List[SummaryResponse]:
        """Process multiple summarization requests concurrently"""
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def summarize_with_semaphore(req):
            async with semaphore:
                return await self.summarize(req)
        
        tasks = [summarize_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch summarization failed for item {i}: {result}")
                # Create fallback response
                fallback = await self._fallback_summary(requests[i], datetime.now())
                processed_results.append(fallback)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _generate_llm_summary(
        self, 
        request: SummaryRequest, 
        content_analysis: Dict[str, Any],
        summary_type: SummaryType
    ) -> str:
        """Generate summary using LLM-Server"""
        
        try:
            # Build prompt from template
            template = self.templates[summary_type]
            prompt = template.format(
                content=request.content,
                length=request.length.value,
                language=request.language,
                content_type=content_analysis.get("content_type", "text"),
                custom_instructions=request.custom_prompt or ""
            )
            
            # Determine optimal model based on content
            model = self._select_optimal_model(content_analysis)
            
            # Make request to LLM-Server
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert summarization AI that creates high-quality, accurate summaries while preserving key information and context."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": self._get_max_tokens_for_length(request.length),
                    "stream": False
                }
                
                async with session.post(
                    f"{self.llm_server_url}/v1/chat/completions",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        summary = result["choices"][0]["message"]["content"].strip()
                        return summary
                    else:
                        logger.warning(f"LLM-Server request failed: {response.status}")
                        return await self._fallback_extractive_summary(request.content)
                        
        except Exception as e:
            logger.error(f"Error calling LLM-Server: {e}")
            return await self._fallback_extractive_summary(request.content)
    
    def _determine_optimal_summary_type(
        self, 
        request: SummaryRequest, 
        content_analysis: Dict[str, Any]
    ) -> SummaryType:
        """Determine the best summary type based on content analysis"""
        
        # If user specified, respect their choice
        if request.summary_type != SummaryType.ABSTRACTIVE:
            return request.summary_type
        
        content_type = content_analysis.get("content_type", "unknown")
        is_code = content_analysis.get("is_code", False)
        is_documentation = content_analysis.get("is_documentation", False)
        
        # Smart type selection based on content
        if is_code:
            return SummaryType.TECHNICAL
        elif is_documentation:
            return SummaryType.STRUCTURED
        elif content_type in ["research", "academic", "scientific"]:
            return SummaryType.STRUCTURED
        elif content_type == "news" or "article" in content_type:
            return SummaryType.ABSTRACTIVE
        elif len(request.content) > 5000:
            return SummaryType.STRUCTURED
        else:
            return SummaryType.ABSTRACTIVE
    
    def _select_optimal_model(self, content_analysis: Dict[str, Any]) -> str:
        """Select the best LLM model based on content characteristics"""
        
        is_code = content_analysis.get("is_code", False)
        complexity = content_analysis.get("complexity_score", 0.0)
        language = content_analysis.get("language")
        
        # Model selection logic
        if is_code:
            return "cline-optimized"  # Best for code understanding
        elif complexity > 0.7:
            return "thinking-enabled"  # For complex reasoning
        elif language and language != "en":
            return "multimodal-enhanced"  # Better multilingual support
        else:
            return "openai-compatible"  # General purpose
    
    def _get_max_tokens_for_length(self, length: SummaryLength) -> int:
        """Get appropriate max tokens for summary length"""
        return {
            SummaryLength.SHORT: 100,
            SummaryLength.MEDIUM: 300,
            SummaryLength.LONG: 800,
            SummaryLength.COMPREHENSIVE: 1500
        }.get(length, 300)
    
    def _generate_cache_key(self, request: SummaryRequest) -> str:
        """Generate cache key for request"""
        content_hash = hashlib.md5(request.content.encode()).hexdigest()[:16]
        params_str = f"{request.summary_type.value}-{request.length.value}-{request.language}"
        return f"{content_hash}-{params_str}"
    
    def _extract_keywords(
        self, 
        content: str, 
        content_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract key terms from content"""
        
        # Use content analysis results if available
        if "keywords" in content_analysis:
            return content_analysis["keywords"]
        
        # Simple keyword extraction fallback
        import re
        words = re.findall(r'\b[A-Za-z]{4,}\b', content.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10] if freq > 1]
    
    def _extract_entities(
        self, 
        content: str, 
        content_analysis: Dict[str, Any]
    ) -> List[str]:
        """Extract named entities from content"""
        
        # Use content analysis results if available
        if "entities" in content_analysis:
            return content_analysis["entities"]
        
        # Simple entity extraction fallback
        import re
        # Extract capitalized words (likely proper nouns)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        return list(set(entities))[:20]  # Limit and deduplicate
    
    def _calculate_confidence_score(
        self, 
        original: str, 
        summary: str, 
        content_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the generated summary"""
        
        # Simple heuristic-based confidence calculation
        orig_len = len(original.split())
        summ_len = len(summary.split())
        
        # Compression ratio (should be reasonable)
        compression_ratio = summ_len / orig_len if orig_len > 0 else 0
        
        # Ideal compression ratio is between 0.1 and 0.3
        if 0.1 <= compression_ratio <= 0.3:
            ratio_score = 1.0
        else:
            ratio_score = max(0.3, 1.0 - abs(compression_ratio - 0.2) * 2)
        
        # Content quality indicators
        complexity_bonus = min(content_analysis.get("complexity_score", 0.5), 1.0) * 0.1
        
        # Length appropriateness
        length_score = 1.0 if 20 <= summ_len <= 500 else 0.7
        
        confidence = (ratio_score * 0.6 + length_score * 0.3 + complexity_bonus)
        return min(confidence, 0.95)  # Cap at 95%
    
    async def _fallback_extractive_summary(self, content: str) -> str:
        """Fallback extractive summarization when LLM fails"""
        
        sentences = content.split('. ')
        if len(sentences) <= 3:
            return content
        
        # Simple extractive approach - take first, middle, and key sentences
        key_sentences = [
            sentences[0],  # First sentence (usually important)
            sentences[len(sentences)//2],  # Middle sentence
            sentences[-2] if len(sentences) > 2 else sentences[-1]  # Near-end sentence
        ]
        
        return '. '.join(key_sentences) + '.'
    
    async def _fallback_summary(
        self, 
        request: SummaryRequest, 
        start_time: datetime
    ) -> SummaryResponse:
        """Create fallback summary when main process fails"""
        
        fallback_text = await self._fallback_extractive_summary(request.content)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return SummaryResponse(
            summary=fallback_text,
            summary_type="extractive_fallback",
            length=request.length.value,
            keywords=[],
            entities=[],
            confidence_score=0.5,
            processing_time=processing_time,
            metadata={
                "fallback": True,
                "error": "LLM summarization failed",
                "content_length": len(request.content)
            }
        )
    
    def _suggest_summary_type_from_metadata(self, metadata: Dict[str, Any]) -> SummaryType:
        """Suggest summary type based on document metadata"""
        
        content_type = metadata.get("content_type", "")
        file_ext = metadata.get("file_extension", "")
        is_code = metadata.get("is_code", False)
        
        if is_code or file_ext in [".py", ".js", ".ts", ".java", ".cpp"]:
            return SummaryType.TECHNICAL
        elif content_type == "documentation":
            return SummaryType.STRUCTURED
        else:
            return SummaryType.ABSTRACTIVE
    
    def _suggest_length_from_content(self, content: str) -> SummaryLength:
        """Suggest appropriate summary length based on content size"""
        
        word_count = len(content.split())
        
        if word_count < 200:
            return SummaryLength.SHORT
        elif word_count < 1000:
            return SummaryLength.MEDIUM
        elif word_count < 5000:
            return SummaryLength.LONG
        else:
            return SummaryLength.COMPREHENSIVE
    
    # Template methods for different summary types
    def _get_extractive_template(self) -> str:
        return """Extract the most important sentences from the following {content_type} content to create a {length} summary in {language}.

Content:
{content}

Instructions:
- Select the most informative and representative sentences
- Preserve the original wording exactly
- Ensure the summary flows logically
- Target {length} length
{custom_instructions}

Summary:"""

    def _get_abstractive_template(self) -> str:
        return """Create a {length} abstractive summary of the following {content_type} content in {language}.

Content:
{content}

Instructions:
- Generate new text that captures the essence of the content
- Be concise while preserving key information
- Use your own words to explain the main concepts
- Target {length} length
{custom_instructions}

Summary:"""

    def _get_structured_template(self) -> str:
        return """Create a {length} structured summary of the following {content_type} content in {language}.

Content:
{content}

Instructions:
- Organize the summary with clear sections/headings
- Include key points in bullet format where appropriate
- Maintain logical flow between sections
- Target {length} length
{custom_instructions}

Summary:"""

    def _get_bullet_points_template(self) -> str:
        return """Create a {length} bullet-point summary of the following {content_type} content in {language}.

Content:
{content}

Instructions:
- Use clear, concise bullet points
- Each bullet should capture a key insight or fact
- Organize bullets by importance or theme
- Target {length} length
{custom_instructions}

Summary:"""

    def _get_technical_template(self) -> str:
        return """Create a {length} technical summary of the following {content_type} content in {language}.

Content:
{content}

Instructions:
- Focus on technical concepts, methods, and implementation details
- Preserve technical terminology and accuracy
- Include relevant code concepts or APIs mentioned
- Target {length} length
{custom_instructions}

Summary:"""

    def _get_narrative_template(self) -> str:
        return """Create a {length} narrative summary of the following {content_type} content in {language}.

Content:
{content}

Instructions:
- Present the summary as a coherent story or explanation
- Maintain chronological or logical flow
- Use engaging language while staying accurate
- Target {length} length
{custom_instructions}

Summary:"""