"""
Late Chunking Preprocessor
Specialized preprocessing for Late Chunking operations - embeddings BEFORE chunking
Optimized for preserving document context and structure
"""

import re
import logging
from typing import Dict, Any, List, Union
from dataclasses import dataclass

logger = logging.getLogger("embedding-hub.late-chunking")

@dataclass
class ChunkingContext:
    """Context information for chunking operations"""
    document_type: str
    total_length: int
    section_boundaries: List[int]
    paragraph_boundaries: List[int]
    sentence_boundaries: List[int]

class LatechunkingPreprocessor:
    """
    Preprocessor specialized for Late Chunking operations
    
    Key principles:
    1. Preserve document structure for optimal chunking
    2. Maintain semantic boundaries
    3. Add contextual markers for chunk relationships
    4. Optimize for post-embedding chunking
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.preprocessing_options = config.get('preprocessing', {}).get('options', {})
        
        # Configuration flags
        self.preserve_paragraphs = self.preprocessing_options.get('preserve_paragraph_boundaries', True)
        self.maintain_structure = self.preprocessing_options.get('maintain_document_structure', True)
        self.context_overlap = self.preprocessing_options.get('context_window_overlap', 128)
        self.sentence_detection = self.preprocessing_options.get('sentence_boundary_detection', True)
        
        logger.info(f"Initialized Late Chunking preprocessor with config: {self.preprocessing_options}")
    
    async def preprocess(self, content: Union[str, bytes], metadata: Dict[str, Any]) -> str:
        """
        Preprocess content for Late Chunking embedding generation
        
        Args:
            content: Raw document content
            metadata: Additional context information
            
        Returns:
            Preprocessed content optimized for Late Chunking
        """
        try:
            # Convert to string if needed
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Analyze document structure
            context = self._analyze_document_structure(content)
            
            # Apply preprocessing steps
            processed_content = content
            
            if self.maintain_structure:
                processed_content = self._preserve_document_structure(processed_content, context)
            
            if self.preserve_paragraphs:
                processed_content = self._preserve_paragraph_boundaries(processed_content)
                
            if self.sentence_detection:
                processed_content = self._add_sentence_markers(processed_content)
            
            # Add contextual information for chunking
            processed_content = self._add_chunking_context(processed_content, context, metadata)
            
            logger.debug(f"Late chunking preprocessing completed - Length: {len(processed_content)}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error in late chunking preprocessing: {e}")
            return content  # Fallback to original content
    
    def _analyze_document_structure(self, content: str) -> ChunkingContext:
        """Analyze document structure to identify optimal chunking boundaries"""
        
        # Detect document type
        doc_type = self._detect_document_type(content)
        
        # Find section boundaries (headers, titles)
        section_boundaries = self._find_section_boundaries(content)
        
        # Find paragraph boundaries
        paragraph_boundaries = self._find_paragraph_boundaries(content)
        
        # Find sentence boundaries
        sentence_boundaries = self._find_sentence_boundaries(content)
        
        return ChunkingContext(
            document_type=doc_type,
            total_length=len(content),
            section_boundaries=section_boundaries,
            paragraph_boundaries=paragraph_boundaries,
            sentence_boundaries=sentence_boundaries
        )
    
    def _detect_document_type(self, content: str) -> str:
        """Detect the type of document for specialized processing"""
        
        # Check for code patterns
        if re.search(r'(def |function |class |\{|\}|import |from )', content):
            return "code"
        
        # Check for markdown patterns
        if re.search(r'(^#{1,6}\s|```|\*\*|\[.*\]\(.*\))', content, re.MULTILINE):
            return "markdown"
            
        # Check for academic/research paper patterns
        if re.search(r'(abstract|introduction|methodology|conclusion|references)', content, re.IGNORECASE):
            return "academic"
            
        # Check for conversation patterns
        if re.search(r'(user:|assistant:|human:|ai:|\n[A-Z][a-z]+:)', content, re.IGNORECASE):
            return "conversation"
            
        return "general_text"
    
    def _find_section_boundaries(self, content: str) -> List[int]:
        """Find section boundaries in the document"""
        boundaries = []
        
        # Look for markdown headers
        for match in re.finditer(r'^#{1,6}\s.*$', content, re.MULTILINE):
            boundaries.append(match.start())
            
        # Look for underlined headers
        for match in re.finditer(r'^.+\n[=-]{3,}$', content, re.MULTILINE):
            boundaries.append(match.start())
            
        # Look for numbered sections
        for match in re.finditer(r'^\d+\.\s+[A-Z].*$', content, re.MULTILINE):
            boundaries.append(match.start())
            
        return sorted(boundaries)
    
    def _find_paragraph_boundaries(self, content: str) -> List[int]:
        """Find paragraph boundaries for structure preservation"""
        boundaries = []
        
        # Find double newlines (paragraph separators)
        for match in re.finditer(r'\n\s*\n', content):
            boundaries.append(match.end())
            
        return boundaries
    
    def _find_sentence_boundaries(self, content: str) -> List[int]:
        """Find sentence boundaries for fine-grained chunking"""
        boundaries = []
        
        # Simple sentence boundary detection
        sentence_endings = re.finditer(r'[.!?]+\s+', content)
        for match in sentence_endings:
            boundaries.append(match.end())
            
        return boundaries
    
    def _preserve_document_structure(self, content: str, context: ChunkingContext) -> str:
        """Add structural markers to preserve document organization"""
        
        processed_content = content
        
        # Add document type marker
        processed_content = f"[DOC_TYPE:{context.document_type.upper()}]\n{processed_content}"
        
        # Add section markers at boundaries
        offset = 0
        for boundary in reversed(context.section_boundaries):  # Reverse to maintain positions
            adjusted_boundary = boundary + offset
            marker = "\n[SECTION_BOUNDARY]\n"
            processed_content = (
                processed_content[:adjusted_boundary] + 
                marker + 
                processed_content[adjusted_boundary:]
            )
            offset += len(marker)
        
        return processed_content
    
    def _preserve_paragraph_boundaries(self, content: str) -> str:
        """Mark paragraph boundaries for chunking awareness"""
        
        # Replace double newlines with paragraph markers
        content = re.sub(r'\n\s*\n', '\n[PARAGRAPH_BREAK]\n', content)
        
        return content
    
    def _add_sentence_markers(self, content: str) -> str:
        """Add subtle sentence markers for fine-grained chunking"""
        
        # Add markers after sentence endings
        content = re.sub(r'([.!?]+)(\s+)', r'\1[SENT_END]\2', content)
        
        return content
    
    def _add_chunking_context(self, content: str, context: ChunkingContext, metadata: Dict[str, Any]) -> str:
        """Add contextual information to optimize chunking"""
        
        # Create context header
        context_header = [
            f"[CHUNKING_CONTEXT]",
            f"Length: {context.total_length}",
            f"Type: {context.document_type}",
            f"Sections: {len(context.section_boundaries)}",
            f"Paragraphs: {len(context.paragraph_boundaries)}",
            f"Sentences: {len(context.sentence_boundaries)}"
        ]
        
        # Add metadata if available
        if metadata:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float)):
                    context_header.append(f"{key}: {value}")
        
        context_header.append("[/CHUNKING_CONTEXT]")
        
        # Combine context with content
        full_content = "\n".join(context_header) + "\n\n" + content
        
        return full_content
    
    def get_chunking_strategy(self, content: str) -> Dict[str, Any]:
        """
        Suggest optimal chunking strategy based on preprocessing analysis
        This can be used by the chunking system after embedding generation
        """
        
        context = self._analyze_document_structure(content)
        
        strategy = {
            "document_type": context.document_type,
            "recommended_chunk_size": self._recommend_chunk_size(context),
            "boundary_preferences": self._get_boundary_preferences(context),
            "overlap_strategy": self._get_overlap_strategy(context),
            "special_handling": self._get_special_handling(context)
        }
        
        return strategy
    
    def _recommend_chunk_size(self, context: ChunkingContext) -> int:
        """Recommend optimal chunk size based on document analysis"""
        
        if context.document_type == "code":
            return 512  # Smaller chunks for code
        elif context.document_type == "academic":
            return 1024  # Larger chunks for academic content
        elif context.document_type == "conversation":
            return 256  # Small chunks for dialogue
        else:
            return 768  # Default chunk size
    
    def _get_boundary_preferences(self, context: ChunkingContext) -> List[str]:
        """Get preferred chunking boundaries in order of preference"""
        
        preferences = []
        
        if len(context.section_boundaries) > 0:
            preferences.append("section")
        
        if len(context.paragraph_boundaries) > 10:  # Only if many paragraphs
            preferences.append("paragraph")
            
        preferences.append("sentence")
        
        return preferences
    
    def _get_overlap_strategy(self, context: ChunkingContext) -> Dict[str, Any]:
        """Recommend overlap strategy for chunks"""
        
        return {
            "overlap_tokens": min(self.context_overlap, context.total_length // 10),
            "overlap_type": "semantic",  # Overlap at semantic boundaries
            "preserve_context": True
        }
    
    def _get_special_handling(self, context: ChunkingContext) -> Dict[str, Any]:
        """Special handling rules for specific document types"""
        
        handling = {}
        
        if context.document_type == "code":
            handling["preserve_function_boundaries"] = True
            handling["include_imports"] = True
            
        elif context.document_type == "conversation":
            handling["preserve_turn_structure"] = True
            handling["include_speaker_context"] = True
            
        elif context.document_type == "academic":
            handling["preserve_citations"] = True
            handling["maintain_argument_flow"] = True
            
        return handling