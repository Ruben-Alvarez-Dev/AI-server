"""
CoRAG Engine - Chain-of-Retrieval Augmented Generation
State-of-the-art 2025 implementation based on Microsoft Research
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import json
import re

logger = logging.getLogger(__name__)

@dataclass
class RetrievalStep:
    """Single step in retrieval chain"""
    query: str
    refined_query: str
    retrieved_docs: List[Dict[str, Any]]
    reasoning: str
    confidence: float

@dataclass
class RetrievalChain:
    """Complete chain of retrievals"""
    original_query: str
    steps: List[RetrievalStep]
    final_synthesis: str
    total_confidence: float

class CoRAGEngine:
    """
    Chain-of-Retrieval Augmented Generation Engine
    Implements iterative retrieval and reasoning for complex queries
    """
    
    def __init__(self, llm_model, vector_store, max_chains: int = 5):
        self.llm_model = llm_model
        self.vector_store = vector_store
        self.max_chains = max_chains
        
        # CoRAG prompts
        self.query_refinement_prompt = """
Given the original query and previous retrieval attempts, refine the search query to find more specific information.

Original Query: {original_query}
Previous Attempts: {previous_attempts}
Current Knowledge Gap: {knowledge_gap}

Generate a refined search query that will help fill this knowledge gap:
Query: """

        self.synthesis_prompt = """
You are an expert at synthesizing information from multiple retrieval steps.

Original Question: {original_query}

Retrieval Chain:
{retrieval_chain}

Based on all the retrieved information above, provide a comprehensive answer that:
1. Addresses the original question completely
2. Uses evidence from multiple sources
3. Shows logical reasoning
4. Acknowledges any limitations or gaps

Answer: """
    
    async def generate_corag_response(
        self, 
        query: str, 
        context: Dict[str, Any] = None
    ) -> RetrievalChain:
        """
        Generate response using Chain-of-Retrieval methodology
        """
        logger.info(f"Starting CoRAG for query: {query}")
        
        retrieval_chain = RetrievalChain(
            original_query=query,
            steps=[],
            final_synthesis="",
            total_confidence=0.0
        )
        
        current_query = query
        previous_knowledge = []
        
        # Iterative retrieval chain
        for step_num in range(self.max_chains):
            logger.info(f"CoRAG Step {step_num + 1}: {current_query}")
            
            # Retrieve documents for current query
            retrieved_docs = await self.vector_store.similarity_search(
                current_query, 
                k=5
            )
            
            # Analyze if we have sufficient information
            analysis = await self._analyze_retrieval_completeness(
                original_query=query,
                current_docs=retrieved_docs,
                previous_knowledge=previous_knowledge
            )
            
            # Create retrieval step
            step = RetrievalStep(
                query=current_query,
                refined_query="",
                retrieved_docs=retrieved_docs,
                reasoning=analysis['reasoning'],
                confidence=analysis['confidence']
            )
            
            retrieval_chain.steps.append(step)
            previous_knowledge.extend(retrieved_docs)
            
            # Check if we have enough information
            if analysis['sufficient'] or step_num == self.max_chains - 1:
                logger.info(f"CoRAG completed after {step_num + 1} steps")
                break
            
            # Refine query for next iteration
            current_query = await self._refine_query(
                original_query=query,
                previous_attempts=[s.query for s in retrieval_chain.steps],
                knowledge_gap=analysis['knowledge_gap']
            )
            
            step.refined_query = current_query
        
        # Final synthesis
        retrieval_chain.final_synthesis = await self._synthesize_chain(retrieval_chain)
        retrieval_chain.total_confidence = self._calculate_total_confidence(retrieval_chain)
        
        logger.info(f"CoRAG synthesis completed with confidence: {retrieval_chain.total_confidence:.2f}")
        
        return retrieval_chain
    
    async def _analyze_retrieval_completeness(
        self, 
        original_query: str, 
        current_docs: List[Dict], 
        previous_knowledge: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze if current retrieval provides sufficient information"""
        
        analysis_prompt = f"""
Analyze if the retrieved information is sufficient to answer the original query.

Original Query: {original_query}

Current Retrieved Documents:
{json.dumps([doc.get('content', '')[:200] + '...' for doc in current_docs], indent=2)}

Previous Knowledge:
{len(previous_knowledge)} documents previously retrieved

Assessment Tasks:
1. Is the information sufficient to answer the query? (yes/no)
2. What specific knowledge gaps remain?
3. Confidence level in current information (0.0-1.0)
4. Reasoning for your assessment

Response format:
{{
    "sufficient": true/false,
    "knowledge_gap": "specific gaps description",
    "confidence": 0.0-1.0,
    "reasoning": "detailed reasoning"
}}
"""
        
        # Use LLM to analyze completeness
        try:
            response = await self._generate_llm_response(analysis_prompt)
            
            # Parse JSON response
            analysis = self._parse_json_response(response)
            
            return {
                'sufficient': analysis.get('sufficient', False),
                'knowledge_gap': analysis.get('knowledge_gap', ''),
                'confidence': analysis.get('confidence', 0.5),
                'reasoning': analysis.get('reasoning', '')
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'sufficient': len(current_docs) > 0,
                'knowledge_gap': 'Unable to analyze',
                'confidence': 0.3,
                'reasoning': 'Analysis failed, using fallback'
            }
    
    async def _refine_query(
        self, 
        original_query: str, 
        previous_attempts: List[str], 
        knowledge_gap: str
    ) -> str:
        """Refine search query based on previous attempts"""
        
        prompt = self.query_refinement_prompt.format(
            original_query=original_query,
            previous_attempts='\n'.join([f"- {attempt}" for attempt in previous_attempts]),
            knowledge_gap=knowledge_gap
        )
        
        try:
            response = await self._generate_llm_response(prompt)
            
            # Extract refined query
            refined = response.strip()
            if refined.startswith("Query:"):
                refined = refined[6:].strip()
            
            return refined
            
        except Exception as e:
            logger.error(f"Query refinement failed: {e}")
            return f"{original_query} {knowledge_gap}"
    
    async def _synthesize_chain(self, chain: RetrievalChain) -> str:
        """Synthesize final response from retrieval chain"""
        
        # Build retrieval chain summary
        chain_summary = ""
        for i, step in enumerate(chain.steps):
            chain_summary += f"\nStep {i+1}: {step.query}\n"
            chain_summary += f"Confidence: {step.confidence:.2f}\n"
            chain_summary += f"Retrieved: {len(step.retrieved_docs)} documents\n"
            
            # Add top documents content
            for j, doc in enumerate(step.retrieved_docs[:2]):  # Top 2 per step
                content = doc.get('content', '')[:300]
                chain_summary += f"  Doc {j+1}: {content}...\n"
        
        prompt = self.synthesis_prompt.format(
            original_query=chain.original_query,
            retrieval_chain=chain_summary
        )
        
        try:
            synthesis = await self._generate_llm_response(prompt)
            return synthesis.strip()
            
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return f"Error synthesizing response: {e}"
    
    def _calculate_total_confidence(self, chain: RetrievalChain) -> float:
        """Calculate overall confidence for the chain"""
        if not chain.steps:
            return 0.0
        
        # Weighted average with more recent steps having higher weight
        total_weighted_confidence = 0.0
        total_weight = 0.0
        
        for i, step in enumerate(chain.steps):
            weight = (i + 1) / len(chain.steps)  # Later steps weighted more
            total_weighted_confidence += step.confidence * weight
            total_weight += weight
        
        return total_weighted_confidence / total_weight if total_weight > 0 else 0.0
    
    async def _generate_llm_response(self, prompt: str) -> str:
        """Generate response using the main LLM"""
        try:
            if self.llm_model is not None:
                # Generate response using llama-cpp-python
                response = self.llm_model(
                    prompt,
                    max_tokens=256,
                    temperature=0.3,
                    stop=["</analysis>", "\n\n---", "Human:"],
                    echo=False
                )
                return response["choices"][0]["text"].strip()
            else:
                # Fallback for testing without model
                return "LLM response placeholder - model not loaded"
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"LLM generation error: {str(e)}"
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            # Find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            logger.error(f"JSON parsing failed: {e}")
            return {
                'sufficient': False,
                'knowledge_gap': 'JSON parsing error',
                'confidence': 0.3,
                'reasoning': f'Failed to parse response: {response[:100]}...'
            }

# Export
__all__ = ['CoRAGEngine', 'RetrievalChain', 'RetrievalStep']