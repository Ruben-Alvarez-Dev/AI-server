#!/usr/bin/env python3
"""
Test script for profile-based model selection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from configs.llama_cpp.optimized_llama import OptimizedLlama, MODEL_POOL
from configs.llama_cpp.m1_ultra_config import M1_ULTRA_CONFIG

def test_profile_detection():
    """Test automatic profile detection"""
    
    test_cases = [
        ("How do I fix this Python function?", "DEV"),
        ("def hello_world():\n    print('Hello')", "DEV"),
        ("The API endpoint returns a 500 error", "DEV"),
        ("What's the weather like today?", "GENERAL"),
        ("Tell me about the history of Rome", "GENERAL"),
        ("import requests\nfrom flask import Flask", "DEV"),
        ("Can you help debug my JavaScript code?", "DEV"),
        ("console.log('testing')", "DEV"),
    ]
    
    config = M1_ULTRA_CONFIG
    
    print("Testing profile auto-detection:")
    print("=" * 50)
    
    for query, expected in test_cases:
        detected = config.detect_profile_from_context(query)
        status = "✅" if detected == expected else "❌"
        print(f"{status} Query: '{query[:30]}...'")
        print(f"   Expected: {expected}, Detected: {detected}")
        print()

def test_model_selection():
    """Test model selection by profile"""
    
    config = M1_ULTRA_CONFIG
    
    print("Testing model selection by profile:")
    print("=" * 50)
    
    profiles = ["DEV", "GENERAL", "CODE", "CHAT", "DEFAULT"]
    
    for profile in profiles:
        model = config.get_model_by_profile(profile)
        print(f"Profile '{profile}': {model}")
    
    print()

def test_optimized_llama_creation():
    """Test OptimizedLlama creation with profiles"""
    
    print("Testing OptimizedLlama creation:")
    print("=" * 50)
    
    try:
        # Test DEV profile
        dev_llama = OptimizedLlama(profile="DEV", auto_detect_profile=False)
        print(f"✅ DEV profile model: {dev_llama.model_path.name}")
        print(f"   Profile: {dev_llama.profile}")
        print(f"   Auto-detect: {dev_llama.auto_detect_profile}")
        
        # Test GENERAL profile
        general_llama = OptimizedLlama(profile="GENERAL", auto_detect_profile=False)
        print(f"✅ GENERAL profile model: {general_llama.model_path.name}")
        print(f"   Profile: {general_llama.profile}")
        
        # Test auto-detection
        auto_llama = OptimizedLlama(profile="GENERAL", auto_detect_profile=True)
        print(f"✅ Auto-detect enabled model: {auto_llama.model_path.name}")
        print(f"   Profile: {auto_llama.profile}")
        print(f"   Auto-detect: {auto_llama.auto_detect_profile}")
        
    except Exception as e:
        print(f"❌ Error creating OptimizedLlama: {e}")
    
    print()

def test_model_info():
    """Test model info with profile data"""
    
    print("Testing model info:")
    print("=" * 50)
    
    try:
        llama = OptimizedLlama(profile="DEV", auto_detect_profile=True)
        info = llama.get_model_info()
        
        print("Model Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"❌ Error getting model info: {e}")

if __name__ == "__main__":
    print("🧪 Profile-based Model Selection Tests")
    print("=" * 60)
    print()
    
    test_profile_detection()
    test_model_selection()
    test_optimized_llama_creation()
    test_model_info()
    
    print("Tests completed! ✨")