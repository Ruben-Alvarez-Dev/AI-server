"""
Modular Memory System - 3-Tier Architecture
State-of-the-art 2025 implementation for unlimited context expansion
"""

import asyncio
import logging
import time
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class MemoryFragment:
    """Single memory fragment with metadata"""
    content: str
    timestamp: float
    importance_score: float
    access_count: int
    last_access: float
    memory_type: str  # 'working', 'episode', 'semantic'
    context_tags: List[str]
    embedding: Optional[List[float]] = None
    fragment_id: Optional[str] = None
    
    def __post_init__(self):
        if self.fragment_id is None:
            self.fragment_id = hashlib.md5(
                f"{self.content}{self.timestamp}".encode()
            ).hexdigest()

@dataclass
class EpisodeCluster:
    """Cluster of related memory fragments forming an episode"""
    episode_id: str
    fragments: List[MemoryFragment]
    start_time: float
    end_time: float
    central_theme: str
    importance_score: float
    access_pattern: Dict[str, int]

@dataclass
class SemanticConcept:
    """High-level semantic concept extracted from episodes"""
    concept_id: str
    name: str
    description: str
    related_episodes: List[str]
    knowledge_graph_nodes: List[str]
    confidence: float
    last_reinforced: float

class ModularMemory:
    """
    3-Tier Modular Memory System
    - Working Memory: 128K context window (immediate access)
    - Episode Memory: 2M+ token clusters (medium-term patterns)
    - Semantic Memory: Unlimited conceptual knowledge (long-term)
    """
    
    def __init__(
        self, 
        working_memory_limit: int = 131072,  # 128K tokens
        episode_memory_limit: int = 2097152,  # 2M tokens
        max_episodes: int = 1000,
        max_concepts: int = 5000
    ):
        # Memory tiers
        self.working_memory: deque = deque(maxlen=working_memory_limit // 100)  # ~100 tokens per fragment
        self.episode_memory: Dict[str, EpisodeCluster] = {}
        self.semantic_memory: Dict[str, SemanticConcept] = {}
        
        # Configuration
        self.working_memory_limit = working_memory_limit
        self.episode_memory_limit = episode_memory_limit
        self.max_episodes = max_episodes
        self.max_concepts = max_concepts
        
        # Memory management
        self.fragment_index: Dict[str, MemoryFragment] = {}
        self.importance_threshold = 0.3
        self.consolidation_interval = 300  # 5 minutes
        self.last_consolidation = time.time()
        
        # Analytics
        self.memory_stats = {
            'fragments_created': 0,
            'episodes_formed': 0,
            'concepts_extracted': 0,
            'consolidations_performed': 0
        }
        
        logger.info(f"ModularMemory initialized: Working={working_memory_limit//1024}K, Episode={episode_memory_limit//1024}K")
    
    async def store_fragment(
        self, 
        content: str, 
        importance_score: float = 0.5,
        context_tags: List[str] = None
    ) -> str:
        """Store new memory fragment in working memory"""
        
        fragment = MemoryFragment(
            content=content,
            timestamp=time.time(),
            importance_score=importance_score,
            access_count=0,
            last_access=time.time(),
            memory_type='working',
            context_tags=context_tags or []
        )
        
        # Add to working memory
        self.working_memory.append(fragment)
        self.fragment_index[fragment.fragment_id] = fragment
        self.memory_stats['fragments_created'] += 1
        
        logger.debug(f"Stored fragment {fragment.fragment_id[:8]}... in working memory")
        
        # Trigger consolidation if needed
        await self._check_consolidation()
        
        return fragment.fragment_id
    
    async def retrieve_relevant(
        self, 
        query: str, 
        max_fragments: int = 20,
        memory_types: List[str] = None
    ) -> List[MemoryFragment]:
        """Retrieve most relevant fragments across all memory tiers"""
        
        if memory_types is None:
            memory_types = ['working', 'episode', 'semantic']
        
        relevant_fragments = []
        
        # Search working memory
        if 'working' in memory_types:
            for fragment in list(self.working_memory):
                relevance = await self._calculate_relevance(query, fragment)
                if relevance > 0.3:
                    fragment.access_count += 1
                    fragment.last_access = time.time()
                    relevant_fragments.append((relevance, fragment))
        
        # Search episode memory
        if 'episode' in memory_types:
            for episode in self.episode_memory.values():
                episode_relevance = await self._calculate_episode_relevance(query, episode)
                if episode_relevance > 0.2:
                    # Add most relevant fragments from episode
                    for fragment in episode.fragments[:3]:  # Top 3 from episode
                        fragment.access_count += 1
                        fragment.last_access = time.time()
                        relevant_fragments.append((episode_relevance * 0.8, fragment))
        
        # Search semantic memory
        if 'semantic' in memory_types:
            semantic_fragments = await self._search_semantic_memory(query)
            relevant_fragments.extend(semantic_fragments)
        
        # Sort by relevance and return top fragments
        relevant_fragments.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Retrieved {len(relevant_fragments)} relevant fragments for query")
        
        return [fragment for _, fragment in relevant_fragments[:max_fragments]]
    
    async def get_context_summary(self, max_tokens: int = 4000) -> str:
        """Generate context summary from all memory tiers"""
        
        # Get recent working memory
        recent_working = list(self.working_memory)[-10:]
        
        # Get most important episodes
        important_episodes = sorted(
            self.episode_memory.values(), 
            key=lambda x: x.importance_score, 
            reverse=True
        )[:5]
        
        # Get key semantic concepts
        key_concepts = sorted(
            self.semantic_memory.values(),
            key=lambda x: x.confidence,
            reverse=True
        )[:10]
        
        # Build context summary
        context_parts = []
        
        # Recent context
        if recent_working:
            context_parts.append("## Recent Context")
            for fragment in recent_working[-5:]:
                context_parts.append(f"- {fragment.content[:200]}...")
        
        # Episode patterns
        if important_episodes:
            context_parts.append("\n## Key Episodes")
            for episode in important_episodes[:3]:
                context_parts.append(f"- {episode.central_theme}: {len(episode.fragments)} fragments")
        
        # Semantic knowledge
        if key_concepts:
            context_parts.append("\n## Known Concepts")
            for concept in key_concepts[:5]:
                context_parts.append(f"- {concept.name}: {concept.description[:100]}...")
        
        summary = "\n".join(context_parts)
        
        # Truncate if needed
        if len(summary) > max_tokens:
            summary = summary[:max_tokens-3] + "..."
        
        return summary
    
    async def _check_consolidation(self):
        """Check if memory consolidation is needed"""
        
        current_time = time.time()
        if current_time - self.last_consolidation > self.consolidation_interval:
            await self._consolidate_memory()
            self.last_consolidation = current_time
    
    async def _consolidate_memory(self):
        """Consolidate working memory into episodes and semantic concepts"""
        
        logger.info("Starting memory consolidation...")
        
        # Move important fragments to episode memory
        working_fragments = list(self.working_memory)
        
        if len(working_fragments) < 5:
            return
        
        # Cluster fragments into episodes
        episodes = await self._cluster_fragments_into_episodes(working_fragments)
        
        for episode in episodes:
            if episode.importance_score > self.importance_threshold:
                self.episode_memory[episode.episode_id] = episode
                
                # Remove fragments from working memory
                for fragment in episode.fragments:
                    fragment.memory_type = 'episode'
                    try:
                        self.working_memory.remove(fragment)
                    except ValueError:
                        pass  # Fragment already removed
        
        # Extract semantic concepts from episodes
        await self._extract_semantic_concepts()
        
        # Cleanup old episodes if needed
        if len(self.episode_memory) > self.max_episodes:
            await self._cleanup_episodes()
        
        self.memory_stats['consolidations_performed'] += 1
        
        logger.info(f"Consolidation complete. Episodes: {len(self.episode_memory)}, Concepts: {len(self.semantic_memory)}")
    
    async def _cluster_fragments_into_episodes(
        self, 
        fragments: List[MemoryFragment]
    ) -> List[EpisodeCluster]:
        """Cluster fragments into coherent episodes"""
        
        if not fragments:
            return []
        
        # Simple time-based clustering for now
        # In production, this would use semantic similarity
        episodes = []
        current_episode_fragments = []
        time_threshold = 600  # 10 minutes
        
        sorted_fragments = sorted(fragments, key=lambda x: x.timestamp)
        
        for fragment in sorted_fragments:
            if not current_episode_fragments:
                current_episode_fragments = [fragment]
            elif fragment.timestamp - current_episode_fragments[-1].timestamp < time_threshold:
                current_episode_fragments.append(fragment)
            else:
                # Create episode from current fragments
                if len(current_episode_fragments) >= 2:
                    episode = await self._create_episode_cluster(current_episode_fragments)
                    episodes.append(episode)
                
                current_episode_fragments = [fragment]
        
        # Handle remaining fragments
        if len(current_episode_fragments) >= 2:
            episode = await self._create_episode_cluster(current_episode_fragments)
            episodes.append(episode)
        
        logger.debug(f"Created {len(episodes)} episodes from {len(fragments)} fragments")
        
        return episodes
    
    async def _create_episode_cluster(self, fragments: List[MemoryFragment]) -> EpisodeCluster:
        """Create episode cluster from fragments"""
        
        episode_id = hashlib.md5(
            f"episode_{fragments[0].timestamp}_{len(fragments)}".encode()
        ).hexdigest()
        
        # Calculate episode metrics
        start_time = min(f.timestamp for f in fragments)
        end_time = max(f.timestamp for f in fragments)
        
        # Extract central theme (simplified)
        central_theme = await self._extract_episode_theme(fragments)
        
        # Calculate importance
        importance_score = sum(f.importance_score for f in fragments) / len(fragments)
        importance_score *= min(len(fragments) / 5, 2.0)  # Bonus for larger episodes
        
        episode = EpisodeCluster(
            episode_id=episode_id,
            fragments=fragments,
            start_time=start_time,
            end_time=end_time,
            central_theme=central_theme,
            importance_score=importance_score,
            access_pattern=defaultdict(int)
        )
        
        self.memory_stats['episodes_formed'] += 1
        
        return episode
    
    async def _extract_episode_theme(self, fragments: List[MemoryFragment]) -> str:
        """Extract central theme from episode fragments"""
        
        # Simple theme extraction - in production use LLM
        all_content = " ".join(f.content for f in fragments)
        
        # Extract most common words (simplified)
        words = all_content.lower().split()
        word_freq = defaultdict(int)
        
        for word in words:
            if len(word) > 4:  # Skip short words
                word_freq[word] += 1
        
        if word_freq:
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
            theme = " ".join([word for word, _ in top_words])
        else:
            theme = f"Episode {fragments[0].timestamp}"
        
        return theme
    
    async def _extract_semantic_concepts(self):
        """Extract high-level concepts from episodes"""
        
        # Analyze episodes to extract recurring patterns
        concept_patterns = defaultdict(list)
        
        for episode in self.episode_memory.values():
            theme_words = episode.central_theme.split()
            for word in theme_words:
                if len(word) > 4:
                    concept_patterns[word].append(episode.episode_id)
        
        # Create semantic concepts for patterns with multiple episodes
        for concept_name, episode_ids in concept_patterns.items():
            if len(episode_ids) >= 2 and concept_name not in self.semantic_memory:
                
                concept = SemanticConcept(
                    concept_id=hashlib.md5(concept_name.encode()).hexdigest(),
                    name=concept_name,
                    description=f"Concept extracted from {len(episode_ids)} episodes",
                    related_episodes=episode_ids,
                    knowledge_graph_nodes=[],
                    confidence=min(len(episode_ids) / 5, 1.0),
                    last_reinforced=time.time()
                )
                
                self.semantic_memory[concept.concept_id] = concept
                self.memory_stats['concepts_extracted'] += 1
    
    async def _cleanup_episodes(self):
        """Remove old, low-importance episodes"""
        
        episodes_by_importance = sorted(
            self.episode_memory.items(),
            key=lambda x: (x[1].importance_score, x[1].end_time)
        )
        
        # Remove least important episodes
        to_remove = len(self.episode_memory) - self.max_episodes
        
        for i in range(to_remove):
            episode_id, episode = episodes_by_importance[i]
            
            # Move fragments back to working memory if very recent
            current_time = time.time()
            for fragment in episode.fragments:
                if current_time - fragment.timestamp < 3600:  # 1 hour
                    fragment.memory_type = 'working'
                    if len(self.working_memory) < self.working_memory.maxlen:
                        self.working_memory.append(fragment)
            
            del self.episode_memory[episode_id]
            
        logger.info(f"Cleaned up {to_remove} old episodes")
    
    async def _calculate_relevance(self, query: str, fragment: MemoryFragment) -> float:
        """Calculate relevance score between query and fragment"""
        
        # Simple keyword matching - in production use embeddings
        query_words = set(query.lower().split())
        fragment_words = set(fragment.content.lower().split())
        
        if not query_words or not fragment_words:
            return 0.0
        
        intersection = query_words.intersection(fragment_words)
        union = query_words.union(fragment_words)
        
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Boost by importance and recency
        importance_boost = fragment.importance_score
        recency_boost = max(0, 1.0 - (time.time() - fragment.timestamp) / 86400)  # 24h decay
        
        relevance = jaccard * (1 + importance_boost + recency_boost * 0.5)
        
        return min(relevance, 1.0)
    
    async def _calculate_episode_relevance(self, query: str, episode: EpisodeCluster) -> float:
        """Calculate relevance score for entire episode"""
        
        theme_relevance = await self._calculate_text_similarity(query, episode.central_theme)
        
        # Check fragment relevance
        fragment_relevances = []
        for fragment in episode.fragments[:5]:  # Sample first 5
            relevance = await self._calculate_relevance(query, fragment)
            fragment_relevances.append(relevance)
        
        avg_fragment_relevance = sum(fragment_relevances) / len(fragment_relevances) if fragment_relevances else 0
        
        # Combine theme and fragment relevance
        total_relevance = (theme_relevance * 0.4 + avg_fragment_relevance * 0.6) * episode.importance_score
        
        return min(total_relevance, 1.0)
    
    async def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _search_semantic_memory(self, query: str) -> List[Tuple[float, MemoryFragment]]:
        """Search semantic memory for relevant concepts"""
        
        relevant_fragments = []
        
        for concept in self.semantic_memory.values():
            concept_relevance = await self._calculate_text_similarity(
                query, 
                f"{concept.name} {concept.description}"
            )
            
            if concept_relevance > 0.2:
                # Find fragments from related episodes
                for episode_id in concept.related_episodes[:2]:  # Top 2 episodes
                    if episode_id in self.episode_memory:
                        episode = self.episode_memory[episode_id]
                        for fragment in episode.fragments[:2]:  # Top 2 fragments
                            adjusted_relevance = concept_relevance * concept.confidence * 0.7
                            relevant_fragments.append((adjusted_relevance, fragment))
        
        return relevant_fragments
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory usage statistics"""
        
        working_size = len(self.working_memory)
        episode_count = len(self.episode_memory)
        concept_count = len(self.semantic_memory)
        
        # Calculate total fragments across all tiers
        total_fragments = working_size
        for episode in self.episode_memory.values():
            total_fragments += len(episode.fragments)
        
        # Memory distribution
        memory_distribution = {
            'working_memory': {
                'fragments': working_size,
                'percentage': working_size / total_fragments * 100 if total_fragments > 0 else 0
            },
            'episode_memory': {
                'episodes': episode_count,
                'fragments': total_fragments - working_size,
                'percentage': (total_fragments - working_size) / total_fragments * 100 if total_fragments > 0 else 0
            },
            'semantic_memory': {
                'concepts': concept_count
            }
        }
        
        return {
            'total_fragments': total_fragments,
            'memory_distribution': memory_distribution,
            'performance_stats': self.memory_stats,
            'consolidation_status': {
                'last_consolidation': self.last_consolidation,
                'time_since_last': time.time() - self.last_consolidation
            }
        }
    
    async def clear_memory(self, memory_type: str = 'all'):
        """Clear specified memory tier"""
        
        if memory_type in ['all', 'working']:
            self.working_memory.clear()
            
        if memory_type in ['all', 'episode']:
            self.episode_memory.clear()
            
        if memory_type in ['all', 'semantic']:
            self.semantic_memory.clear()
            
        if memory_type == 'all':
            self.fragment_index.clear()
            
        logger.info(f"Cleared {memory_type} memory")

# Export
__all__ = ['ModularMemory', 'MemoryFragment', 'EpisodeCluster', 'SemanticConcept']