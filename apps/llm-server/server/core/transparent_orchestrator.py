"""
Transparent Orchestrator - Cline-style Internal Process Visibility
Shows all AI thoughts, planning, and decision-making in real-time
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ThoughtType(Enum):
    """Types of internal AI thoughts"""
    ANALYSIS = "analysis"
    PLANNING = "planning"  
    DECISION = "decision"
    REASONING = "reasoning"
    REFLECTION = "reflection"
    ERROR = "error"
    INSIGHT = "insight"
    STRATEGY = "strategy"

@dataclass
class AIThought:
    """Individual AI thought or internal process"""
    thought_id: str
    agent_name: str
    thought_type: ThoughtType
    title: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    reasoning_chain: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'thought_id': self.thought_id,
            'agent_name': self.agent_name,
            'thought_type': self.thought_type.value,
            'title': self.title,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context,
            'confidence': self.confidence,
            'reasoning_chain': self.reasoning_chain
        }

class TransparentOrchestrator:
    """
    Transparent AI Orchestrator
    
    Makes all AI internal processes visible like Cline:
    - Shows planning thoughts
    - Reveals decision-making process
    - Displays reasoning chains
    - Exposes error handling
    - Shows strategy adjustments
    """
    
    def __init__(self):
        self.thought_stream: List[AIThought] = []
        self.active_contexts: Dict[str, Dict[str, Any]] = {}
        self.transparency_callbacks = []
        
    def add_transparency_callback(self, callback):
        """Add callback for real-time thought streaming"""
        self.transparency_callbacks.append(callback)
    
    async def think_aloud(
        self,
        agent_name: str,
        thought_type: ThoughtType,
        title: str,
        content: str,
        context: Dict[str, Any] = None,
        confidence: float = 1.0,
        reasoning_chain: List[str] = None
    ) -> str:
        """Make AI thought visible to user (like Cline's internal process)"""
        
        thought = AIThought(
            thought_id=f"{agent_name}_{int(time.time() * 1000)}",
            agent_name=agent_name,
            thought_type=thought_type,
            title=title,
            content=content,
            context=context or {},
            confidence=confidence,
            reasoning_chain=reasoning_chain or []
        )
        
        self.thought_stream.append(thought)
        
        # Broadcast to all transparency callbacks
        for callback in self.transparency_callbacks:
            try:
                await callback(thought)
            except Exception as e:
                logger.error(f"Transparency callback failed: {e}")
        
        return thought.thought_id
    
    async def show_planning_process(
        self,
        agent_name: str,
        task_description: str,
        initial_thoughts: List[str],
        planning_steps: List[Dict[str, Any]]
    ):
        """Show detailed planning process like Cline"""
        
        # Initial analysis
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.ANALYSIS,
            title="🔍 Analyzing Task Requirements",
            content=f"Breaking down the request: '{task_description}'\n\nInitial thoughts:\n" + 
                   "\n".join([f"• {thought}" for thought in initial_thoughts]),
            context={'task': task_description}
        )
        
        # Planning breakdown
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.PLANNING,
            title="📋 Creating Implementation Plan",
            content="I need to break this down into manageable steps:\n\n" +
                   "\n".join([
                       f"{i+1}. **{step['title']}**\n   {step['description']}\n   Agent: {step['agent']}\n   Estimated: {step.get('time', 'TBD')}"
                       for i, step in enumerate(planning_steps)
                   ]),
            context={'planning_steps': planning_steps}
        )
        
        # Strategy decision
        strategy_reasoning = [
            "Evaluating different approaches",
            "Considering resource constraints and capabilities",
            "Optimizing for parallel execution where possible",
            "Ensuring quality gates at each step"
        ]
        
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.STRATEGY,
            title="🎯 Execution Strategy",
            content="Based on my analysis, here's my execution strategy:\n\n" +
                   "✅ Use specialized agents for optimal results\n" +
                   "✅ Implement TDD approach with tests first\n" +
                   "✅ Enable parallel execution where dependencies allow\n" +
                   "✅ Include quality verification at each stage",
            reasoning_chain=strategy_reasoning,
            confidence=0.9
        )
    
    async def show_decision_making(
        self,
        agent_name: str,
        decision_context: str,
        options: List[Dict[str, Any]],
        chosen_option: str,
        reasoning: List[str]
    ):
        """Show decision-making process transparently"""
        
        options_text = "\n".join([
            f"**Option {i+1}: {opt['name']}**\n" +
            f"   Pros: {', '.join(opt.get('pros', []))}\n" +
            f"   Cons: {', '.join(opt.get('cons', []))}\n" +
            f"   Confidence: {opt.get('confidence', 'Unknown')}"
            for i, opt in enumerate(options)
        ])
        
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.DECISION,
            title="🤔 Making Decision",
            content=f"Context: {decision_context}\n\n" +
                   f"Available options:\n{options_text}\n\n" +
                   f"**Decision: {chosen_option}**\n\n" +
                   "Reasoning:\n" + "\n".join([f"• {reason}" for reason in reasoning]),
            context={
                'decision_context': decision_context,
                'options': options,
                'chosen_option': chosen_option
            },
            reasoning_chain=reasoning
        )
    
    async def show_problem_solving(
        self,
        agent_name: str,
        problem: str,
        analysis: List[str],
        solution_approach: str,
        implementation_notes: List[str]
    ):
        """Show problem-solving thought process"""
        
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.REASONING,
            title="🧩 Problem Solving",
            content=f"**Problem:** {problem}\n\n" +
                   "**Analysis:**\n" + "\n".join([f"• {point}" for point in analysis]) + "\n\n" +
                   f"**Solution Approach:** {solution_approach}\n\n" +
                   "**Implementation Notes:**\n" + "\n".join([f"• {note}" for note in implementation_notes]),
            context={'problem': problem, 'solution': solution_approach},
            reasoning_chain=analysis + [solution_approach]
        )
    
    async def show_error_handling(
        self,
        agent_name: str,
        error: str,
        error_analysis: List[str],
        recovery_plan: str,
        prevention_measures: List[str]
    ):
        """Show error handling and recovery process"""
        
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.ERROR,
            title="⚠️ Error Handling",
            content=f"**Error Encountered:** {error}\n\n" +
                   "**Analysis:**\n" + "\n".join([f"• {point}" for point in error_analysis]) + "\n\n" +
                   f"**Recovery Plan:** {recovery_plan}\n\n" +
                   "**Prevention Measures:**\n" + "\n".join([f"• {measure}" for measure in prevention_measures]),
            context={'error': error, 'recovery_plan': recovery_plan},
            confidence=0.8
        )
    
    async def show_reflection(
        self,
        agent_name: str,
        completed_action: str,
        what_worked: List[str],
        what_could_improve: List[str],
        lessons_learned: List[str]
    ):
        """Show post-action reflection and learning"""
        
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.REFLECTION,
            title="💭 Reflection & Learning",
            content=f"**Completed:** {completed_action}\n\n" +
                   "**What Worked Well:**\n" + "\n".join([f"✅ {item}" for item in what_worked]) + "\n\n" +
                   "**Areas for Improvement:**\n" + "\n".join([f"🔄 {item}" for item in what_could_improve]) + "\n\n" +
                   "**Lessons Learned:**\n" + "\n".join([f"💡 {lesson}" for lesson in lessons_learned]),
            context={'action': completed_action}
        )
    
    async def show_insight(
        self,
        agent_name: str,
        insight_title: str,
        insight_content: str,
        implications: List[str],
        action_items: List[str]
    ):
        """Show new insights or discoveries"""
        
        await self.think_aloud(
            agent_name=agent_name,
            thought_type=ThoughtType.INSIGHT,
            title=f"💡 {insight_title}",
            content=f"{insight_content}\n\n" +
                   "**Implications:**\n" + "\n".join([f"→ {imp}" for imp in implications]) + "\n\n" +
                   "**Action Items:**\n" + "\n".join([f"🎯 {item}" for item in action_items]),
            context={'insight': insight_title}
        )
    
    def get_thought_stream(
        self,
        agent_name: str = None,
        thought_type: ThoughtType = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get filtered thought stream"""
        
        filtered_thoughts = self.thought_stream
        
        if agent_name:
            filtered_thoughts = [t for t in filtered_thoughts if t.agent_name == agent_name]
        
        if thought_type:
            filtered_thoughts = [t for t in filtered_thoughts if t.thought_type == thought_type]
        
        # Sort by timestamp (newest first) and limit
        filtered_thoughts = sorted(
            filtered_thoughts,
            key=lambda t: t.timestamp,
            reverse=True
        )[:limit]
        
        return [t.to_dict() for t in filtered_thoughts]
    
    def get_agent_context(self, agent_name: str) -> Dict[str, Any]:
        """Get current context for an agent"""
        return self.active_contexts.get(agent_name, {})
    
    def update_agent_context(self, agent_name: str, context: Dict[str, Any]):
        """Update agent context"""
        if agent_name not in self.active_contexts:
            self.active_contexts[agent_name] = {}
        self.active_contexts[agent_name].update(context)
    
    async def stream_thoughts_to_console(self) -> AsyncGenerator[str, None]:
        """Stream thoughts to console in real-time (like Cline)"""
        
        last_thought_count = 0
        
        while True:
            current_count = len(self.thought_stream)
            
            if current_count > last_thought_count:
                # New thoughts available
                new_thoughts = self.thought_stream[last_thought_count:]
                
                for thought in new_thoughts:
                    # Format thought for console output
                    timestamp = thought.timestamp.strftime("%H:%M:%S")
                    icon = self._get_thought_icon(thought.thought_type)
                    
                    console_output = f"\n{icon} [{timestamp}] {thought.agent_name} - {thought.title}\n"
                    console_output += f"   {thought.content}\n"
                    
                    if thought.reasoning_chain:
                        console_output += f"   Reasoning: {' → '.join(thought.reasoning_chain[:3])}...\n"
                    
                    if thought.confidence < 1.0:
                        console_output += f"   Confidence: {thought.confidence:.1%}\n"
                    
                    yield console_output
                
                last_thought_count = current_count
            
            await asyncio.sleep(0.1)  # Check for new thoughts every 100ms
    
    def _get_thought_icon(self, thought_type: ThoughtType) -> str:
        """Get emoji icon for thought type"""
        icons = {
            ThoughtType.ANALYSIS: "🔍",
            ThoughtType.PLANNING: "📋", 
            ThoughtType.DECISION: "🤔",
            ThoughtType.REASONING: "🧩",
            ThoughtType.REFLECTION: "💭",
            ThoughtType.ERROR: "⚠️",
            ThoughtType.INSIGHT: "💡",
            ThoughtType.STRATEGY: "🎯"
        }
        return icons.get(thought_type, "🤖")
    
    def clear_thought_stream(self, older_than_hours: int = 24):
        """Clear old thoughts to manage memory"""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        
        self.thought_stream = [
            t for t in self.thought_stream 
            if t.timestamp.timestamp() > cutoff_time
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get thought stream statistics"""
        
        if not self.thought_stream:
            return {'total_thoughts': 0}
        
        # Count by type
        type_counts = {}
        agent_counts = {}
        
        for thought in self.thought_stream:
            type_counts[thought.thought_type.value] = type_counts.get(thought.thought_type.value, 0) + 1
            agent_counts[thought.agent_name] = agent_counts.get(thought.agent_name, 0) + 1
        
        # Calculate average confidence
        confidences = [t.confidence for t in self.thought_stream if t.confidence < 1.0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 1.0
        
        return {
            'total_thoughts': len(self.thought_stream),
            'thoughts_by_type': type_counts,
            'thoughts_by_agent': agent_counts,
            'average_confidence': avg_confidence,
            'active_contexts': len(self.active_contexts),
            'oldest_thought': self.thought_stream[0].timestamp.isoformat() if self.thought_stream else None,
            'newest_thought': self.thought_stream[-1].timestamp.isoformat() if self.thought_stream else None
        }

# Global transparent orchestrator instance
transparency = TransparentOrchestrator()

# Decorator for making agent methods transparent
def make_transparent(thought_type: ThoughtType = ThoughtType.REASONING):
    """Decorator to make agent methods show their internal process"""
    
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            agent_name = getattr(self, 'name', self.__class__.__name__)
            
            # Show that we're starting to think about this
            await transparency.think_aloud(
                agent_name=agent_name,
                thought_type=ThoughtType.ANALYSIS,
                title=f"Starting {func.__name__}",
                content=f"About to execute {func.__name__} with parameters",
                context={'function': func.__name__, 'args': str(args)[:200]}
            )
            
            try:
                result = await func(self, *args, **kwargs)
                
                # Show successful completion
                await transparency.think_aloud(
                    agent_name=agent_name,
                    thought_type=ThoughtType.INSIGHT,
                    title=f"Completed {func.__name__}",
                    content=f"Successfully completed {func.__name__}",
                    context={'function': func.__name__, 'success': True}
                )
                
                return result
                
            except Exception as e:
                # Show error handling
                await transparency.show_error_handling(
                    agent_name=agent_name,
                    error=str(e),
                    error_analysis=[f"Error in {func.__name__}", f"Error type: {type(e).__name__}"],
                    recovery_plan="Attempting graceful error handling",
                    prevention_measures=["Add better input validation", "Improve error handling"]
                )
                raise
        
        return wrapper
    return decorator

# Export
__all__ = ['TransparentOrchestrator', 'AIThought', 'ThoughtType', 'transparency', 'make_transparent']