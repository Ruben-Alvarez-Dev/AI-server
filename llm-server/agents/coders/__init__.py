"""
Coder Agents Module - Specialized coding agents for different development tasks

This module provides two specialized coding agents:
- PrimaryCoderAgent: High-performance coding using Qwen2.5-Coder-7B (88.4% HumanEval)
- SecondaryCoderAgent: Efficient backup coding using DeepSeek-Coder-V2-16B (MoE)
"""

from .base_coder import (
    BaseCoderAgent,
    CodeRequest,
    CodeResponse,
    CodeLanguage,
    CodeTaskType
)

from .primary_coder import (
    PrimaryCoderAgent,
    get_primary_coder_agent
)

from .secondary_coder import (
    SecondaryCoderAgent,
    get_secondary_coder_agent
)

__all__ = [
    # Base classes
    "BaseCoderAgent",
    "CodeRequest", 
    "CodeResponse",
    "CodeLanguage",
    "CodeTaskType",
    
    # Agent implementations
    "PrimaryCoderAgent",
    "SecondaryCoderAgent",
    
    # Factory functions
    "get_primary_coder_agent",
    "get_secondary_coder_agent"
]