"""
Conversation Preprocessor
Specialized preprocessing for dialogue, chat history, and conversational context
Optimized for conversational flow and turn-taking patterns
"""

import re
import logging
from typing import Dict, Any, List, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("embedding-hub.conversation")

@dataclass
class ConversationContext:
    """Context information for conversation processing"""
    total_turns: int
    speakers: List[str]
    turn_lengths: List[int]
    dialogue_flow_score: float
    temporal_markers: List[str]
    topics: List[str]

class ConversationPreprocessor:
    """
    Preprocessor specialized for conversational content embedding generation
    
    Key principles:
    1. Preserve dialogue flow and turn-taking structure
    2. Maintain speaker identity and context
    3. Extract conversational patterns and intentions
    4. Handle temporal relationships between exchanges
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.preprocessing_options = config.get('preprocessing', {}).get('options', {})
        
        # Configuration flags
        self.preserve_turn_structure = self.preprocessing_options.get('preserve_turn_structure', True)
        self.include_speaker_information = self.preprocessing_options.get('include_speaker_information', True)
        self.temporal_awareness = self.preprocessing_options.get('temporal_awareness', True)
        self.context_window_turns = self.preprocessing_options.get('context_window_turns', 10)
        self.emotion_detection = self.preprocessing_options.get('emotion_detection', False)
        
        # Speaker patterns
        self.speaker_patterns = [
            r'^([A-Z][a-zA-Z]*\d*):\s*',           # Speaker: format
            r'^([A-Z][a-zA-Z]*)\s*>>\s*',          # Speaker >> format
            r'^\[([A-Z][a-zA-Z]*)\]\s*',           # [Speaker] format
            r'^<([A-Z][a-zA-Z]*)>\s*',             # <Speaker> format
            r'^(\w+):\s*',                         # Generic word: format
        ]
        
        logger.info(f"Initialized Conversation preprocessor with context window: {self.context_window_turns}")
    
    async def preprocess(self, content: Union[str, bytes], metadata: Dict[str, Any]) -> str:
        """
        Preprocess conversational content for embedding generation
        
        Args:
            content: Raw conversation content
            metadata: Additional context information
            
        Returns:
            Preprocessed content optimized for conversational understanding
        """
        try:
            # Convert to string if needed
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Analyze conversation structure
            context = self._analyze_conversation_structure(content)
            
            # Apply preprocessing steps
            processed_content = content
            
            if self.preserve_turn_structure:
                processed_content = self._preserve_turn_structure(processed_content, context)
                
            if self.include_speaker_information:
                processed_content = self._enhance_speaker_information(processed_content, context)
            
            if self.temporal_awareness:
                processed_content = self._add_temporal_markers(processed_content, context, metadata)
            
            # Add conversational context for embeddings
            processed_content = self._add_conversational_context(processed_content, context, metadata)
            
            logger.debug(f"Conversation preprocessing completed - Turns: {context.total_turns}, Speakers: {len(context.speakers)}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error in conversation preprocessing: {e}")
            return content  # Fallback to original content
    
    def _analyze_conversation_structure(self, content: str) -> ConversationContext:
        """Analyze conversation structure to extract dialogue patterns"""
        
        # Find dialogue turns
        turns = self._extract_dialogue_turns(content)
        
        # Identify unique speakers
        speakers = self._identify_speakers(content)
        
        # Analyze turn lengths
        turn_lengths = [len(turn.split()) for turn in turns]
        
        # Calculate dialogue flow score
        flow_score = self._calculate_dialogue_flow(turns)
        
        # Extract temporal markers
        temporal_markers = self._extract_temporal_markers(content)
        
        # Identify conversation topics
        topics = self._extract_topics(content)
        
        return ConversationContext(
            total_turns=len(turns),
            speakers=speakers,
            turn_lengths=turn_lengths,
            dialogue_flow_score=flow_score,
            temporal_markers=temporal_markers,
            topics=topics
        )
    
    def _extract_dialogue_turns(self, content: str) -> List[str]:
        """Extract individual dialogue turns from conversation"""
        turns = []
        
        # Split by speaker patterns
        for pattern in self.speaker_patterns:
            if re.search(pattern, content, re.MULTILINE):
                parts = re.split(pattern, content, flags=re.MULTILINE)
                # Filter out empty parts and speaker names
                turns = [part.strip() for part in parts if part.strip() and not re.match(r'^[A-Z][a-zA-Z]*\d*$', part)]
                break
        
        # If no speaker patterns found, split by line breaks
        if not turns:
            turns = [line.strip() for line in content.split('\n') if line.strip()]
        
        return turns
    
    def _identify_speakers(self, content: str) -> List[str]:
        """Identify unique speakers in the conversation"""
        speakers = set()
        
        for pattern in self.speaker_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            speakers.update(matches)
        
        # Common speaker identifiers if no patterns match
        if not speakers:
            common_speakers = ['User', 'Assistant', 'Human', 'AI', 'Bot', 'Agent']
            for speaker in common_speakers:
                if speaker.lower() in content.lower():
                    speakers.add(speaker)
        
        return list(speakers)
    
    def _calculate_dialogue_flow(self, turns: List[str]) -> float:
        """Calculate dialogue flow quality score"""
        if len(turns) < 2:
            return 0.0
        
        # Analyze turn transitions
        transition_score = 0.0
        
        for i in range(len(turns) - 1):
            current_turn = turns[i].lower()
            next_turn = turns[i + 1].lower()
            
            # Look for question-answer patterns
            if ('?' in current_turn and 
                any(word in next_turn for word in ['yes', 'no', 'because', 'that', 'it'])):
                transition_score += 1.0
            
            # Look for continuation markers
            if any(marker in next_turn for marker in ['also', 'additionally', 'furthermore', 'however']):
                transition_score += 0.5
        
        # Normalize by number of transitions
        return transition_score / max(len(turns) - 1, 1)
    
    def _extract_temporal_markers(self, content: str) -> List[str]:
        """Extract temporal markers from conversation"""
        temporal_patterns = [
            r'\b(yesterday|today|tomorrow|now|then|later|before|after)\b',
            r'\b(\d{1,2}:\d{2}(?:\s?[AP]M)?)\b',  # Time stamps
            r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',     # Dates
            r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b'
        ]
        
        markers = []
        for pattern in temporal_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            markers.extend(matches)
        
        return list(set(markers))
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics from conversation"""
        # Simple topic extraction based on frequent nouns
        import re
        
        # Remove common conversational words
        stop_words = {
            'i', 'you', 'we', 'they', 'he', 'she', 'it', 'that', 'this', 'the', 'a', 'an',
            'and', 'or', 'but', 'so', 'yes', 'no', 'ok', 'okay', 'well', 'um', 'uh'
        }
        
        # Extract potential topic words (capitalized words and technical terms)
        topic_words = re.findall(r'\b[A-Z][a-z]+\b|\b\w+(?:ing|tion|ment|ness|ity)\b', content)
        topic_words = [word.lower() for word in topic_words if word.lower() not in stop_words]
        
        # Count frequency and return top topics
        from collections import Counter
        word_counts = Counter(topic_words)
        topics = [word for word, count in word_counts.most_common(5) if count > 1]
        
        return topics
    
    def _preserve_turn_structure(self, content: str, context: ConversationContext) -> str:
        """Add markers to preserve dialogue turn structure"""
        
        # Add turn markers
        processed_lines = []
        
        for pattern in self.speaker_patterns:
            if re.search(pattern, content, re.MULTILINE):
                # Split and reconstruct with turn markers
                lines = content.split('\n')
                for line in lines:
                    if re.match(pattern, line):
                        processed_lines.append(f"[TURN_START]{line}[TURN_CONTENT]")
                    elif line.strip():
                        processed_lines.append(line)
                    else:
                        processed_lines.append("[TURN_END]")
                break
        
        if not processed_lines:
            # No speaker patterns, treat each non-empty line as a turn
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    processed_lines.append(f"[TURN_{i}]{line}")
                else:
                    processed_lines.append("")
        
        return '\n'.join(processed_lines)
    
    def _enhance_speaker_information(self, content: str, context: ConversationContext) -> str:
        """Enhance speaker information for better context understanding"""
        
        processed_content = content
        
        # Add speaker context information
        if len(context.speakers) > 1:
            speaker_info = f"[SPEAKERS: {', '.join(context.speakers[:5])}]"  # Limit to 5 speakers
            processed_content = f"{speaker_info}\n{processed_content}"
        
        # Enhance speaker transitions
        for i, speaker in enumerate(context.speakers):
            # Mark speaker changes with context
            speaker_pattern = f"{speaker}:"
            if speaker_pattern in processed_content:
                processed_content = processed_content.replace(
                    speaker_pattern,
                    f"[SPEAKER_{i}:{speaker}]"
                )
        
        return processed_content
    
    def _add_temporal_markers(self, content: str, context: ConversationContext, metadata: Dict[str, Any]) -> str:
        """Add temporal awareness markers"""
        
        processed_content = content
        
        # Add timestamp information if available
        if metadata and 'timestamp' in metadata:
            timestamp = metadata['timestamp']
            processed_content = f"[TIMESTAMP: {timestamp}]\n{processed_content}"
        
        # Mark temporal references
        for marker in context.temporal_markers:
            if marker in processed_content:
                processed_content = processed_content.replace(
                    marker, 
                    f"[TEMPORAL:{marker}]"
                )
        
        return processed_content
    
    def _add_conversational_context(self, content: str, context: ConversationContext, metadata: Dict[str, Any]) -> str:
        """Add comprehensive conversational context for embeddings"""
        
        # Create context header
        context_header = [
            "[CONVERSATION_CONTEXT]",
            f"Turns: {context.total_turns}",
            f"Speakers: {len(context.speakers)}",
            f"Avg_Turn_Length: {sum(context.turn_lengths) / max(len(context.turn_lengths), 1):.1f}",
            f"Dialogue_Flow: {context.dialogue_flow_score:.2f}"
        ]
        
        # Add speaker information
        if context.speakers:
            context_header.append(f"Speaker_List: {', '.join(context.speakers[:3])}")
        
        # Add topics if identified
        if context.topics:
            context_header.append(f"Topics: {', '.join(context.topics[:3])}")
        
        # Add temporal markers
        if context.temporal_markers:
            context_header.append(f"Temporal_Markers: {len(context.temporal_markers)}")
        
        # Add metadata if available
        if metadata:
            for key, value in metadata.items():
                if key in ['chat_type', 'platform', 'conversation_id'] and isinstance(value, str):
                    context_header.append(f"{key}: {value}")
        
        context_header.append("[/CONVERSATION_CONTEXT]")
        
        # Combine context with content
        full_content = "\n".join(context_header) + "\n\n" + content
        
        return full_content
    
    def extract_conversation_features(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured features from conversation for specialized processing
        """
        
        context = self._analyze_conversation_structure(content)
        
        features = {
            "conversation_type": self._classify_conversation_type(content),
            "structure": {
                "total_turns": context.total_turns,
                "unique_speakers": len(context.speakers),
                "average_turn_length": sum(context.turn_lengths) / max(len(context.turn_lengths), 1),
                "dialogue_flow_score": context.dialogue_flow_score
            },
            "participants": {
                "speakers": context.speakers[:10],  # Limit for size
                "turn_distribution": self._calculate_turn_distribution(content, context.speakers)
            },
            "temporal": {
                "temporal_markers": context.temporal_markers[:10],
                "has_timestamps": len([m for m in context.temporal_markers if ':' in m or '/' in m]) > 0
            },
            "content": {
                "topics": context.topics[:5],
                "question_count": len(re.findall(r'\?', content)),
                "exclamation_count": len(re.findall(r'!', content)),
                "total_words": len(content.split())
            }
        }
        
        return features
    
    def _classify_conversation_type(self, content: str) -> str:
        """Classify the type of conversation"""
        
        content_lower = content.lower()
        
        # Check for Q&A patterns
        if content_lower.count('?') > content_lower.count('.') * 0.3:
            return "qa_session"
        
        # Check for technical discussion
        tech_indicators = ['code', 'function', 'api', 'database', 'server', 'algorithm', 'implementation']
        if sum(1 for indicator in tech_indicators if indicator in content_lower) >= 3:
            return "technical_discussion"
        
        # Check for customer support
        support_indicators = ['problem', 'issue', 'help', 'support', 'error', 'fix', 'solution']
        if sum(1 for indicator in support_indicators if indicator in content_lower) >= 2:
            return "customer_support"
        
        # Check for casual chat
        casual_indicators = ['how are you', 'what\'s up', 'thanks', 'bye', 'hello', 'hi']
        if sum(1 for indicator in casual_indicators if indicator in content_lower) >= 1:
            return "casual_chat"
        
        return "general_conversation"
    
    def _calculate_turn_distribution(self, content: str, speakers: List[str]) -> Dict[str, int]:
        """Calculate how many turns each speaker has"""
        
        distribution = {speaker: 0 for speaker in speakers}
        
        for pattern in self.speaker_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if match in distribution:
                    distribution[match] += 1
        
        return distribution