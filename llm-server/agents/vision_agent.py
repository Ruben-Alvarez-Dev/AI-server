"""
Vision Agent - Screenshot Analysis and OCR for Development
Specialized agent for analyzing code screenshots, UI components, and error messages
"""

import asyncio
import logging
import base64
import io
import time
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json

# Computer vision imports
try:
    from PIL import Image, ImageEnhance
    import numpy as np
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available, image processing will be limited")

# OCR and ML imports
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama not available, using fallback vision processing")

logger = logging.getLogger(__name__)

class VisionAnalysisResult:
    """Result of vision analysis"""
    
    def __init__(
        self,
        description: str,
        confidence: float,
        detected_text: str = "",
        code_elements: List[str] = None,
        ui_elements: List[str] = None,
        errors_detected: List[str] = None,
        suggestions: List[str] = None,
        processing_time: float = 0.0
    ):
        self.description = description
        self.confidence = confidence
        self.detected_text = detected_text
        self.code_elements = code_elements or []
        self.ui_elements = ui_elements or []
        self.errors_detected = errors_detected or []
        self.suggestions = suggestions or []
        self.processing_time = processing_time
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'description': self.description,
            'confidence': self.confidence,
            'detected_text': self.detected_text,
            'code_elements': self.code_elements,
            'ui_elements': self.ui_elements,
            'errors_detected': self.errors_detected,
            'suggestions': self.suggestions,
            'processing_time': self.processing_time
        }

class VisionAgent:
    """
    Vision Agent for Screenshot Analysis and OCR
    
    Capabilities:
    - Code screenshot analysis
    - Error message detection
    - UI component identification
    - Text extraction (OCR)
    - Code suggestion generation
    - FullHD image processing
    """
    
    def __init__(
        self,
        model_name: str = "moondream:latest",
        max_image_size: Tuple[int, int] = (1920, 1080),  # FullHD
        enable_preprocessing: bool = True
    ):
        self.model_name = model_name
        self.max_image_size = max_image_size
        self.enable_preprocessing = enable_preprocessing
        
        # Analysis templates
        self.analysis_prompts = {
            'code_analysis': """
            Analyze this code screenshot and provide:
            1. Description of what the code does
            2. Any visible errors or issues
            3. Code elements you can identify (functions, classes, variables)
            4. Suggestions for improvements
            5. Extract any visible text/code
            
            Focus on being accurate and helpful for development tasks.
            """,
            
            'error_analysis': """
            This appears to be an error screenshot. Please:
            1. Identify the type of error
            2. Extract the exact error message
            3. Suggest potential causes
            4. Recommend solutions
            5. Identify the programming language/framework if visible
            
            Be precise with error details.
            """,
            
            'ui_analysis': """
            Analyze this UI screenshot and provide:
            1. Description of the interface
            2. UI components visible (buttons, forms, menus, etc.)
            3. Any usability issues or suggestions
            4. Text content extraction
            5. Layout and design observations
            
            Focus on UI/UX aspects.
            """,
            
            'general_ocr': """
            Extract all visible text from this image accurately.
            Preserve formatting, line breaks, and structure as much as possible.
            If there's code, maintain indentation and syntax structure.
            """
        }
        
        # Statistics
        self.stats = {
            'images_processed': 0,
            'total_processing_time': 0.0,
            'successful_analyses': 0,
            'errors': 0,
            'avg_confidence': 0.0
        }
        
        # Initialize vision model
        asyncio.create_task(self._initialize_model())
        
        logger.info(f"VisionAgent initialized with model: {model_name}")
    
    async def _initialize_model(self):
        """Initialize the vision model"""
        
        if not OLLAMA_AVAILABLE:
            logger.error("Ollama not available, vision capabilities will be limited")
            return
        
        try:
            # Check if model is available
            models = ollama.list()
            model_names = [model['name'] for model in models.get('models', [])]
            
            if self.model_name not in model_names:
                logger.info(f"Downloading vision model: {self.model_name}")
                ollama.pull(self.model_name)
            
            # Test the model
            test_result = ollama.generate(
                model=self.model_name,
                prompt="Test",
                options={'num_predict': 10}
            )
            
            logger.info(f"Vision model {self.model_name} is ready")
            
        except Exception as e:
            logger.error(f"Failed to initialize vision model: {e}")
            # Fallback to text-only processing
    
    async def analyze_screenshot(
        self,
        image_path: str,
        analysis_type: str = "code_analysis",
        custom_prompt: str = None
    ) -> VisionAnalysisResult:
        """
        Analyze a screenshot with specified analysis type
        
        Args:
            image_path: Path to the image file
            analysis_type: Type of analysis ('code_analysis', 'error_analysis', 'ui_analysis', 'general_ocr')
            custom_prompt: Custom prompt for analysis
        """
        start_time = time.time()
        
        try:
            # Load and preprocess image
            image = await self._load_and_preprocess_image(image_path)
            
            if image is None:
                return VisionAnalysisResult(
                    "Failed to load image",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            # Get analysis prompt
            prompt = custom_prompt or self.analysis_prompts.get(analysis_type, self.analysis_prompts['code_analysis'])
            
            # Perform vision analysis
            result = await self._analyze_with_model(image, prompt, analysis_type)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(result.confidence, processing_time, success=True)
            result.processing_time = processing_time
            
            logger.info(f"Screenshot analyzed: {image_path} ({analysis_type}) - confidence: {result.confidence:.2f}")
            
            return result
            
        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            self._update_stats(0.0, time.time() - start_time, success=False)
            
            return VisionAnalysisResult(
                f"Analysis failed: {str(e)}",
                confidence=0.0,
                processing_time=time.time() - start_time
            )
    
    async def _load_and_preprocess_image(self, image_path: str) -> Optional[Image.Image]:
        """Load and preprocess image for analysis"""
        
        if not PIL_AVAILABLE:
            logger.error("PIL not available for image processing")
            return None
        
        try:
            image_path = Path(image_path)
            
            if not image_path.exists():
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Load image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (maintain aspect ratio)
            if image.size[0] > self.max_image_size[0] or image.size[1] > self.max_image_size[1]:
                image.thumbnail(self.max_image_size, Image.Resampling.LANCZOS)
                logger.info(f"Image resized to: {image.size}")
            
            # Preprocessing for better OCR
            if self.enable_preprocessing:
                image = await self._enhance_image_for_ocr(image)
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to load/preprocess image: {e}")
            return None
    
    async def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR accuracy"""
        
        try:
            # Enhance contrast for better text recognition
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.1)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    async def _analyze_with_model(
        self,
        image: Image.Image,
        prompt: str,
        analysis_type: str
    ) -> VisionAnalysisResult:
        """Perform analysis using the vision model"""
        
        if not OLLAMA_AVAILABLE:
            return await self._fallback_analysis(image, prompt, analysis_type)
        
        try:
            # Convert image to base64
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            image_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Generate response with vision model
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt,
                images=[image_b64],
                options={
                    'temperature': 0.1,  # Low temperature for precise analysis
                    'num_predict': 2048,  # Allow longer responses
                }
            )
            
            # Parse response
            analysis_text = response['response']
            
            # Extract structured information
            result = await self._parse_analysis_response(analysis_text, analysis_type)
            
            return result
            
        except Exception as e:
            logger.error(f"Model analysis failed: {e}")
            return VisionAnalysisResult(
                f"Model analysis error: {str(e)}",
                confidence=0.2
            )
    
    async def _fallback_analysis(
        self,
        image: Image.Image,
        prompt: str,
        analysis_type: str
    ) -> VisionAnalysisResult:
        """Fallback analysis when vision model is not available"""
        
        # Basic image analysis without ML model
        width, height = image.size
        
        description = f"Image analysis (fallback mode): {width}x{height} pixels"
        
        if analysis_type == "error_analysis":
            description = "Error screenshot detected - vision model needed for detailed analysis"
        elif analysis_type == "ui_analysis":
            description = f"UI screenshot detected - {width}x{height} resolution"
        elif analysis_type == "code_analysis":
            description = "Code screenshot detected - vision model needed for code extraction"
        
        return VisionAnalysisResult(
            description=description,
            confidence=0.3,
            suggestions=["Install vision model for detailed analysis"]
        )
    
    async def _parse_analysis_response(
        self,
        response_text: str,
        analysis_type: str
    ) -> VisionAnalysisResult:
        """Parse the model response into structured data"""
        
        # Extract different sections from the response
        lines = response_text.split('\n')
        
        description = ""
        detected_text = ""
        code_elements = []
        ui_elements = []
        errors_detected = []
        suggestions = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Identify sections
            if any(keyword in line.lower() for keyword in ['description:', 'summary:', 'overview:']):
                current_section = 'description'
                description += line.split(':', 1)[-1].strip() + " "
            elif any(keyword in line.lower() for keyword in ['text:', 'code:', 'extracted:']):
                current_section = 'text'
            elif any(keyword in line.lower() for keyword in ['error:', 'issue:', 'problem:']):
                current_section = 'errors'
            elif any(keyword in line.lower() for keyword in ['suggestion:', 'recommendation:', 'solution:']):
                current_section = 'suggestions'
            elif any(keyword in line.lower() for keyword in ['function:', 'class:', 'variable:', 'method:']):
                current_section = 'code_elements'
            elif any(keyword in line.lower() for keyword in ['button:', 'menu:', 'form:', 'ui:']):
                current_section = 'ui_elements'
            else:
                # Add to current section
                if current_section == 'description':
                    description += line + " "
                elif current_section == 'text':
                    detected_text += line + "\n"
                elif current_section == 'errors':
                    errors_detected.append(line)
                elif current_section == 'suggestions':
                    suggestions.append(line)
                elif current_section == 'code_elements':
                    code_elements.append(line)
                elif current_section == 'ui_elements':
                    ui_elements.append(line)
                else:
                    # If no section identified, add to description
                    description += line + " "
        
        # Clean up
        description = description.strip() or response_text[:200] + "..."
        detected_text = detected_text.strip()
        
        # Calculate confidence based on response quality
        confidence = self._calculate_confidence(response_text, analysis_type)
        
        return VisionAnalysisResult(
            description=description,
            confidence=confidence,
            detected_text=detected_text,
            code_elements=code_elements,
            ui_elements=ui_elements,
            errors_detected=errors_detected,
            suggestions=suggestions
        )
    
    def _calculate_confidence(self, response_text: str, analysis_type: str) -> float:
        """Calculate confidence score for the analysis"""
        
        base_confidence = 0.7
        
        # Adjust based on response length and content
        if len(response_text) < 50:
            base_confidence -= 0.3
        elif len(response_text) > 200:
            base_confidence += 0.1
        
        # Check for specific keywords that indicate good analysis
        quality_indicators = {
            'code_analysis': ['function', 'variable', 'error', 'syntax', 'import'],
            'error_analysis': ['error', 'exception', 'failed', 'traceback', 'line'],
            'ui_analysis': ['button', 'form', 'menu', 'interface', 'layout'],
            'general_ocr': ['text', 'content', 'extracted']
        }
        
        indicators = quality_indicators.get(analysis_type, [])
        found_indicators = sum(1 for keyword in indicators if keyword in response_text.lower())
        
        if found_indicators > 0:
            base_confidence += min(0.2, found_indicators * 0.05)
        
        return min(1.0, max(0.1, base_confidence))
    
    def _update_stats(self, confidence: float, processing_time: float, success: bool):
        """Update processing statistics"""
        
        self.stats['images_processed'] += 1
        self.stats['total_processing_time'] += processing_time
        
        if success:
            self.stats['successful_analyses'] += 1
            # Update average confidence
            total_confidence = self.stats['avg_confidence'] * (self.stats['successful_analyses'] - 1) + confidence
            self.stats['avg_confidence'] = total_confidence / self.stats['successful_analyses']
        else:
            self.stats['errors'] += 1
    
    async def batch_analyze(
        self,
        image_paths: List[str],
        analysis_type: str = "code_analysis"
    ) -> List[VisionAnalysisResult]:
        """Analyze multiple images in batch"""
        
        logger.info(f"Starting batch analysis of {len(image_paths)} images")
        
        results = []
        
        # Process images concurrently (with limit to avoid overwhelming the system)
        semaphore = asyncio.Semaphore(3)  # Limit concurrent analyses
        
        async def analyze_single(path: str) -> VisionAnalysisResult:
            async with semaphore:
                return await self.analyze_screenshot(path, analysis_type)
        
        # Create tasks for all images
        tasks = [analyze_single(path) for path in image_paths]
        
        # Wait for all analyses to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        filtered_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch analysis failed for {image_paths[i]}: {result}")
                filtered_results.append(VisionAnalysisResult(
                    f"Analysis failed: {str(result)}",
                    confidence=0.0
                ))
            else:
                filtered_results.append(result)
        
        logger.info(f"Batch analysis completed: {len(filtered_results)} results")
        
        return filtered_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        
        stats = self.stats.copy()
        
        if stats['images_processed'] > 0:
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['images_processed']
            stats['success_rate'] = stats['successful_analyses'] / stats['images_processed']
        else:
            stats['avg_processing_time'] = 0.0
            stats['success_rate'] = 0.0
        
        return stats
    
    async def quick_ocr(self, image_path: str) -> str:
        """Quick OCR extraction without full analysis"""
        
        result = await self.analyze_screenshot(image_path, "general_ocr")
        return result.detected_text

# Export
__all__ = ['VisionAgent', 'VisionAnalysisResult']