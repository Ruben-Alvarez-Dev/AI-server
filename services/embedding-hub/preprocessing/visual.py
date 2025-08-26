"""
Visual Preprocessor
Specialized preprocessing for screenshots, diagrams, and visual UI content
Optimized for multimodal understanding and visual-text integration
"""

import re
import logging
import base64
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from pathlib import Path
import json

logger = logging.getLogger("embedding-hub.visual")

@dataclass
class VisualContext:
    """Context information for visual content processing"""
    image_format: str
    dimensions: Optional[tuple]
    has_text_overlay: bool
    ui_elements: List[str]
    color_profile: str
    estimated_complexity: float
    text_regions: List[Dict[str, Any]]

class VisualPreprocessor:
    """
    Preprocessor specialized for visual content embedding generation
    
    Key principles:
    1. Extract and preserve textual content within images
    2. Identify UI elements and layout structure
    3. Maintain spatial relationships between elements
    4. Optimize for multimodal understanding
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.preprocessing_options = config.get('preprocessing', {}).get('options', {})
        
        # Configuration flags
        self.image_resize = self.preprocessing_options.get('image_resize', [768, 768])
        self.extract_text_overlay = self.preprocessing_options.get('extract_text_overlay', True)
        self.ui_element_detection = self.preprocessing_options.get('ui_element_detection', True)
        self.preserve_layout_information = self.preprocessing_options.get('preserve_layout_information', True)
        self.supported_formats = self.preprocessing_options.get('supported_formats', 
                                                               ['png', 'jpg', 'jpeg', 'webp'])
        
        # UI element patterns for screenshots
        self.ui_patterns = {
            'button': r'(?i)\b(?:button|btn|click|submit|save|cancel|ok|apply)\b',
            'menu': r'(?i)\b(?:menu|dropdown|select|option|choice)\b',
            'input': r'(?i)\b(?:input|field|text|enter|type|search)\b',
            'navigation': r'(?i)\b(?:nav|navigation|link|home|back|next|previous)\b',
            'dialog': r'(?i)\b(?:dialog|modal|popup|alert|confirm|warning)\b',
            'tab': r'(?i)\b(?:tab|panel|section|page|view)\b',
            'list': r'(?i)\b(?:list|item|row|entry|record)\b',
            'icon': r'(?i)\b(?:icon|symbol|logo|image|picture)\b'
        }
        
        # Code editor patterns
        self.code_patterns = {
            'editor': r'(?i)\b(?:editor|ide|vscode|vim|emacs|sublime)\b',
            'syntax': r'(?i)\b(?:syntax|highlight|color|theme)\b',
            'line_numbers': r'(?i)\b(?:line|number|ln|#)\b',
            'function': r'\b(?:def|function|class|method|var|let|const)\b',
            'keyword': r'\b(?:if|else|for|while|import|from|return)\b'
        }
        
        logger.info(f"Initialized Visual preprocessor for formats: {self.supported_formats}")
    
    async def preprocess(self, content: Union[str, bytes], metadata: Dict[str, Any]) -> str:
        """
        Preprocess visual content for embedding generation
        
        Args:
            content: Raw visual content (image data or description)
            metadata: Additional context information
            
        Returns:
            Preprocessed content optimized for multimodal understanding
        """
        try:
            # Handle different input types
            if isinstance(content, bytes):
                # Image data - convert to description
                processed_content = self._process_image_data(content, metadata)
            elif isinstance(content, str):
                if content.startswith('data:image') or content.startswith('/'):
                    # Image path or data URL
                    processed_content = self._process_image_reference(content, metadata)
                else:
                    # Text description of visual content
                    processed_content = content
            else:
                processed_content = str(content)
            
            # Analyze visual context
            context = self._analyze_visual_context(processed_content, metadata)
            
            # Apply preprocessing steps
            if self.extract_text_overlay and context.has_text_overlay:
                processed_content = self._enhance_text_extraction(processed_content, context)
            
            if self.ui_element_detection:
                processed_content = self._detect_ui_elements(processed_content, context)
            
            if self.preserve_layout_information:
                processed_content = self._preserve_layout_structure(processed_content, context)
            
            # Add visual context for embeddings
            processed_content = self._add_visual_context(processed_content, context, metadata)
            
            logger.debug(f"Visual preprocessing completed - Format: {context.image_format}, UI Elements: {len(context.ui_elements)}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error in visual preprocessing: {e}")
            return str(content)  # Fallback to string representation
    
    def _process_image_data(self, image_data: bytes, metadata: Dict[str, Any]) -> str:
        """Process raw image data and generate description"""
        
        # For now, create a structured description based on metadata and basic analysis
        # In a full implementation, this would use image analysis libraries
        
        description_parts = ["[VISUAL_CONTENT]"]
        
        # Add format information
        if 'content_type' in metadata:
            content_type = metadata['content_type']
            if 'image/' in content_type:
                image_format = content_type.split('/')[-1]
                description_parts.append(f"Format: {image_format.upper()}")
        
        # Add size information if available
        if 'size' in metadata:
            description_parts.append(f"Size: {metadata['size']} bytes")
        
        # Estimate image content based on common patterns
        estimated_content = self._estimate_image_content(image_data, metadata)
        description_parts.extend(estimated_content)
        
        description_parts.append("[/VISUAL_CONTENT]")
        
        return "\n".join(description_parts)
    
    def _process_image_reference(self, image_ref: str, metadata: Dict[str, Any]) -> str:
        """Process image path or data URL reference"""
        
        description_parts = ["[IMAGE_REFERENCE]"]
        
        if image_ref.startswith('data:image'):
            # Data URL
            try:
                header, data = image_ref.split(',', 1)
                format_info = header.split(';')[0].split(':')[1]
                description_parts.append(f"Type: Data URL ({format_info})")
                description_parts.append(f"Data_Length: {len(data)}")
            except:
                description_parts.append("Type: Data URL (unknown format)")
        else:
            # File path
            path = Path(image_ref)
            description_parts.append(f"Path: {path.name}")
            if path.suffix:
                description_parts.append(f"Format: {path.suffix[1:].upper()}")
        
        description_parts.append("[/IMAGE_REFERENCE]")
        
        return "\n".join(description_parts)
    
    def _estimate_image_content(self, image_data: bytes, metadata: Dict[str, Any]) -> List[str]:
        """Estimate image content based on size and metadata patterns"""
        
        content_estimates = []
        data_size = len(image_data)
        
        # Size-based estimates
        if data_size < 50000:  # < 50KB
            content_estimates.append("Estimated_Complexity: Simple (icon, small UI element)")
        elif data_size < 500000:  # < 500KB
            content_estimates.append("Estimated_Complexity: Medium (screenshot, diagram)")
        else:
            content_estimates.append("Estimated_Complexity: High (detailed screenshot, image)")
        
        # Metadata-based estimates
        if metadata:
            filename = metadata.get('filename', '').lower()
            
            if any(term in filename for term in ['screenshot', 'screen', 'capture']):
                content_estimates.append("Content_Type: Screenshot")
            elif any(term in filename for term in ['code', 'editor', 'vscode', 'ide']):
                content_estimates.append("Content_Type: Code Editor Screenshot")
            elif any(term in filename for term in ['ui', 'interface', 'app', 'web']):
                content_estimates.append("Content_Type: User Interface")
            elif any(term in filename for term in ['diagram', 'chart', 'graph', 'flow']):
                content_estimates.append("Content_Type: Diagram/Chart")
            else:
                content_estimates.append("Content_Type: General Image")
        
        return content_estimates
    
    def _analyze_visual_context(self, content: str, metadata: Dict[str, Any]) -> VisualContext:
        """Analyze visual content to extract context information"""
        
        # Detect image format
        image_format = self._detect_image_format(content, metadata)
        
        # Check for text overlay indicators
        has_text = self._detect_text_content(content)
        
        # Identify UI elements
        ui_elements = self._identify_ui_elements(content)
        
        # Estimate dimensions (placeholder - would use actual image analysis)
        dimensions = metadata.get('dimensions', None)
        
        # Determine color profile (placeholder)
        color_profile = self._estimate_color_profile(content)
        
        # Calculate complexity score
        complexity = self._calculate_visual_complexity(content, ui_elements)
        
        # Extract text regions (placeholder)
        text_regions = self._extract_text_regions(content)
        
        return VisualContext(
            image_format=image_format,
            dimensions=dimensions,
            has_text_overlay=has_text,
            ui_elements=ui_elements,
            color_profile=color_profile,
            estimated_complexity=complexity,
            text_regions=text_regions
        )
    
    def _detect_image_format(self, content: str, metadata: Dict[str, Any]) -> str:
        """Detect image format from content and metadata"""
        
        # Check metadata first
        if metadata:
            if 'content_type' in metadata and 'image/' in metadata['content_type']:
                return metadata['content_type'].split('/')[-1]
            
            filename = metadata.get('filename', '')
            if filename:
                suffix = Path(filename).suffix.lower()
                if suffix in ['.png', '.jpg', '.jpeg', '.webp', '.gif']:
                    return suffix[1:]
        
        # Check content for format indicators
        if 'PNG' in content or 'png' in content:
            return 'png'
        elif 'JPEG' in content or 'jpg' in content:
            return 'jpeg'
        elif 'WebP' in content or 'webp' in content:
            return 'webp'
        
        return 'unknown'
    
    def _detect_text_content(self, content: str) -> bool:
        """Detect if visual content likely contains text"""
        
        text_indicators = [
            'text', 'font', 'label', 'title', 'heading', 'caption',
            'code', 'syntax', 'editor', 'terminal', 'console'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in text_indicators)
    
    def _identify_ui_elements(self, content: str) -> List[str]:
        """Identify UI elements in visual content"""
        
        ui_elements = []
        content_lower = content.lower()
        
        # Check UI patterns
        for element_type, pattern in self.ui_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                ui_elements.append(element_type)
        
        # Check code editor patterns
        for element_type, pattern in self.code_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                ui_elements.append(f"code_{element_type}")
        
        return ui_elements
    
    def _estimate_color_profile(self, content: str) -> str:
        """Estimate color profile of visual content"""
        
        content_lower = content.lower()
        
        if any(term in content_lower for term in ['dark', 'black', 'night', 'theme']):
            return 'dark'
        elif any(term in content_lower for term in ['light', 'white', 'bright']):
            return 'light'
        else:
            return 'mixed'
    
    def _calculate_visual_complexity(self, content: str, ui_elements: List[str]) -> float:
        """Calculate visual complexity score"""
        
        complexity_score = 0.0
        
        # Base complexity from UI elements
        complexity_score += len(ui_elements) * 0.5
        
        # Add complexity for specific element types
        complex_elements = ['dialog', 'menu', 'navigation', 'code_editor']
        complexity_score += sum(1.0 for element in ui_elements if element in complex_elements)
        
        # Add complexity for text content
        if self._detect_text_content(content):
            complexity_score += 1.0
        
        # Add complexity for code content
        if any(term in content.lower() for term in ['code', 'syntax', 'function', 'class']):
            complexity_score += 1.5
        
        # Normalize to 0-10 scale
        return min(complexity_score, 10.0)
    
    def _extract_text_regions(self, content: str) -> List[Dict[str, Any]]:
        """Extract text regions from visual content (placeholder implementation)"""
        
        text_regions = []
        
        # Look for text-like patterns in the description
        text_patterns = [
            r'(?i)\b(?:text|label|title|heading|caption):\s*(.+?)(?:\n|$)',
            r'(?i)\b(?:says|shows|displays):\s*["\'](.+?)["\']',
            r'(?i)\b(?:content|message):\s*(.+?)(?:\n|$)'
        ]
        
        for i, pattern in enumerate(text_patterns):
            matches = re.findall(pattern, content)
            for match in matches:
                text_regions.append({
                    'id': f'region_{len(text_regions)}',
                    'text': match.strip(),
                    'type': f'extracted_{i}',
                    'confidence': 0.8
                })
        
        return text_regions[:5]  # Limit to 5 regions
    
    def _enhance_text_extraction(self, content: str, context: VisualContext) -> str:
        """Enhance text extraction from visual content"""
        
        if not context.text_regions:
            return content
        
        # Add extracted text information
        text_section = ["[EXTRACTED_TEXT]"]
        
        for region in context.text_regions:
            text_section.append(f"Region: {region['text']}")
        
        text_section.append("[/EXTRACTED_TEXT]")
        
        return content + "\n" + "\n".join(text_section)
    
    def _detect_ui_elements(self, content: str, context: VisualContext) -> str:
        """Add UI element detection markers"""
        
        if not context.ui_elements:
            return content
        
        # Add UI elements section
        ui_section = ["[UI_ELEMENTS]"]
        
        # Group elements by category
        ui_categories = {}
        for element in context.ui_elements:
            category = element.split('_')[0] if '_' in element else 'general'
            if category not in ui_categories:
                ui_categories[category] = []
            ui_categories[category].append(element)
        
        for category, elements in ui_categories.items():
            ui_section.append(f"{category.title()}: {', '.join(elements)}")
        
        ui_section.append("[/UI_ELEMENTS]")
        
        return content + "\n" + "\n".join(ui_section)
    
    def _preserve_layout_structure(self, content: str, context: VisualContext) -> str:
        """Add layout structure preservation markers"""
        
        # Add layout information based on context
        layout_section = ["[LAYOUT_INFO]"]
        
        if context.dimensions:
            layout_section.append(f"Dimensions: {context.dimensions[0]}x{context.dimensions[1]}")
        
        layout_section.append(f"Complexity: {context.estimated_complexity:.1f}/10")
        layout_section.append(f"Color_Profile: {context.color_profile}")
        
        if context.ui_elements:
            layout_section.append(f"UI_Element_Count: {len(context.ui_elements)}")
        
        if context.text_regions:
            layout_section.append(f"Text_Region_Count: {len(context.text_regions)}")
        
        layout_section.append("[/LAYOUT_INFO]")
        
        return content + "\n" + "\n".join(layout_section)
    
    def _add_visual_context(self, content: str, context: VisualContext, metadata: Dict[str, Any]) -> str:
        """Add comprehensive visual context for embeddings"""
        
        # Create context header
        context_header = [
            "[VISUAL_CONTEXT]",
            f"Format: {context.image_format}",
            f"Complexity: {context.estimated_complexity:.2f}",
            f"Has_Text: {context.has_text_overlay}",
            f"UI_Elements: {len(context.ui_elements)}",
            f"Color_Profile: {context.color_profile}"
        ]
        
        # Add dimensions if available
        if context.dimensions:
            context_header.append(f"Dimensions: {context.dimensions[0]}x{context.dimensions[1]}")
        
        # Add UI element categories
        if context.ui_elements:
            unique_categories = list(set([
                elem.split('_')[0] if '_' in elem else elem 
                for elem in context.ui_elements
            ]))
            context_header.append(f"UI_Categories: {', '.join(unique_categories[:5])}")
        
        # Add text region count
        if context.text_regions:
            context_header.append(f"Text_Regions: {len(context.text_regions)}")
        
        # Add metadata if available
        if metadata:
            if 'source' in metadata:
                context_header.append(f"Source: {metadata['source']}")
            if 'screenshot_type' in metadata:
                context_header.append(f"Screenshot_Type: {metadata['screenshot_type']}")
        
        context_header.append("[/VISUAL_CONTEXT]")
        
        # Combine context with content
        full_content = "\n".join(context_header) + "\n\n" + content
        
        return full_content
    
    def extract_visual_features(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured features from visual content for specialized processing
        """
        
        context = self._analyze_visual_context(content, metadata)
        
        features = {
            "visual_type": self._classify_visual_type(content, context),
            "format": {
                "image_format": context.image_format,
                "dimensions": context.dimensions,
                "estimated_size": self._estimate_file_size(context)
            },
            "content_analysis": {
                "has_text": context.has_text_overlay,
                "text_regions": len(context.text_regions),
                "ui_elements": len(context.ui_elements),
                "complexity_score": context.estimated_complexity
            },
            "ui_structure": {
                "element_types": context.ui_elements[:10],
                "is_code_editor": any('code' in elem for elem in context.ui_elements),
                "is_application_ui": any(elem in ['button', 'menu', 'dialog'] for elem in context.ui_elements)
            },
            "visual_properties": {
                "color_profile": context.color_profile,
                "estimated_text_density": len(context.text_regions) / max(context.estimated_complexity, 1)
            }
        }
        
        return features
    
    def _classify_visual_type(self, content: str, context: VisualContext) -> str:
        """Classify the type of visual content"""
        
        content_lower = content.lower()
        
        # Check for code editor
        if any('code' in elem for elem in context.ui_elements):
            return "code_editor_screenshot"
        
        # Check for application UI
        if len(context.ui_elements) >= 3:
            return "application_interface"
        
        # Check for diagram/chart
        if any(term in content_lower for term in ['diagram', 'chart', 'graph', 'flow']):
            return "diagram_chart"
        
        # Check for web page
        if any(elem in context.ui_elements for elem in ['navigation', 'menu', 'link']):
            return "web_page_screenshot"
        
        # Check for simple screenshot
        if 'screenshot' in content_lower or 'capture' in content_lower:
            return "general_screenshot"
        
        return "general_image"
    
    def _estimate_file_size(self, context: VisualContext) -> str:
        """Estimate file size category based on complexity and format"""
        
        if context.estimated_complexity < 3:
            return "small"
        elif context.estimated_complexity < 7:
            return "medium"
        else:
            return "large"