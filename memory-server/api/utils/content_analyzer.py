"""
Content Analyzer for Memory-Server
Intelligent content analysis and auto-tagging system
"""

import re
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import base64
import hashlib

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger("content-analyzer")
config = get_config()

class ContentAnalyzer:
    """Analyzes content for automatic tagging and categorization"""
    
    def __init__(self):
        # Programming language patterns
        self.language_patterns = {
            'python': [r'def\s+\w+', r'import\s+\w+', r'from\s+\w+\s+import', r'class\s+\w+', r'if\s+__name__\s*==\s*["\']__main__["\']'],
            'javascript': [r'function\s+\w+', r'const\s+\w+', r'let\s+\w+', r'var\s+\w+', r'=>', r'console\.log'],
            'typescript': [r'interface\s+\w+', r'type\s+\w+', r'enum\s+\w+', r':\s*string', r':\s*number', r':\s*boolean'],
            'java': [r'public\s+class', r'private\s+\w+', r'public\s+static\s+void\s+main', r'@Override', r'System\.out\.println'],
            'cpp': [r'#include\s*<', r'std::', r'int\s+main', r'using\s+namespace', r'cout\s*<<'],
            'rust': [r'fn\s+\w+', r'let\s+mut', r'use\s+\w+', r'struct\s+\w+', r'impl\s+\w+'],
            'go': [r'func\s+\w+', r'package\s+\w+', r'import\s+\(', r'var\s+\w+', r'fmt\.Println'],
            'sql': [r'SELECT\s+', r'FROM\s+\w+', r'WHERE\s+', r'INSERT\s+INTO', r'CREATE\s+TABLE'],
            'html': [r'<html', r'<div', r'<script', r'<!DOCTYPE', r'<body>'],
            'css': [r'\{[^}]*\}', r'@media', r'\.[\w-]+\s*\{', r'#[\w-]+\s*\{'],
            'markdown': [r'^#+\s', r'\*\*.*\*\*', r'```', r'\[.*\]\(.*\)', r'^\*\s+'],
            'yaml': [r'---', r'^\s*\w+:\s*$', r'^\s*-\s+'],
            'json': [r'^\s*\{', r'^\s*\[', r'"\w+":\s*', r'},\s*$'],
            'dockerfile': [r'^FROM\s+', r'^RUN\s+', r'^COPY\s+', r'^EXPOSE\s+'],
            'bash': [r'#!/bin/bash', r'\$\w+', r'if\s+\[', r'for\s+\w+\s+in']
        }
        
        # Content type patterns
        self.content_patterns = {
            'documentation': [r'# .*', r'## .*', r'### .*', r'README', r'CHANGELOG', r'API', r'documentation', r'guide', r'tutorial'],
            'configuration': [r'config', r'settings', r'\.env', r'\.ini', r'\.toml', r'\.yaml', r'\.yml', r'\.conf'],
            'testing': [r'test_', r'_test', r'spec\.', r'\.spec', r'describe\(', r'it\(', r'assert', r'expect\('],
            'api': [r'endpoint', r'router', r'@app\.', r'@route', r'GET', r'POST', r'PUT', r'DELETE', r'API'],
            'database': [r'migration', r'schema', r'model', r'entity', r'repository', r'query', r'database'],
            'frontend': [r'component', r'react', r'vue', r'angular', r'jsx', r'tsx', r'css', r'scss', r'html'],
            'backend': [r'server', r'service', r'controller', r'middleware', r'handler', r'route'],
            'devops': [r'docker', r'kubernetes', r'terraform', r'ansible', r'jenkins', r'pipeline', r'deploy'],
            'research': [r'paper', r'study', r'research', r'analysis', r'experiment', r'methodology', r'results'],
            'academic': [r'abstract', r'introduction', r'conclusion', r'bibliography', r'citation', r'thesis'],
            'tutorial': [r'step\s+\d+', r'tutorial', r'how\s+to', r'guide', r'walkthrough', r'example', r'demo'],
            'log': [r'\d{4}-\d{2}-\d{2}', r'ERROR', r'WARNING', r'INFO', r'DEBUG', r'TRACE', r'log'],
            'commit': [r'feat:', r'fix:', r'docs:', r'refactor:', r'test:', r'chore:', r'commit', r'Merge'],
            'issue': [r'bug', r'issue', r'problem', r'error', r'fix', r'resolve', r'closes', r'fixes'],
        }
        
        # Framework/library patterns
        self.framework_patterns = {
            'fastapi': [r'FastAPI', r'@app\.', r'Pydantic', r'BaseModel', r'APIRouter'],
            'flask': [r'Flask', r'@app\.route', r'request', r'session', r'render_template'],
            'django': [r'Django', r'models\.Model', r'views\.', r'urls\.py', r'settings\.py'],
            'react': [r'React', r'useState', r'useEffect', r'JSX', r'Component', r'props'],
            'vue': [r'Vue', r'<template>', r'<script>', r'v-for', r'v-if', r'computed'],
            'angular': [r'Angular', r'@Component', r'@Injectable', r'@NgModule', r'ngOnInit'],
            'express': [r'express', r'app\.get', r'app\.post', r'req\.\w+', r'res\.\w+'],
            'pytorch': [r'torch', r'nn\.Module', r'tensor', r'autograd', r'DataLoader'],
            'tensorflow': [r'tensorflow', r'tf\.', r'keras', r'Sequential', r'layers'],
            'pandas': [r'pandas', r'pd\.', r'DataFrame', r'read_csv', r'groupby'],
            'numpy': [r'numpy', r'np\.', r'array', r'ndarray', r'reshape'],
        }
        
        # Multimodal file types
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.ico'}
        self.video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        self.audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
        self.document_extensions = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'}
        
    async def analyze_content(
        self, 
        content: Union[str, bytes], 
        filename: str = "",
        file_path: Optional[str] = None,
        workspace: str = "research"
    ) -> Dict[str, Any]:
        """
        Comprehensive content analysis
        
        Returns:
            {
                'content_type': 'text'|'image'|'multimodal',
                'file_type': 'python'|'markdown'|etc,
                'auto_tags': ['programming', 'fastapi', etc],
                'language': 'python'|'javascript'|etc,
                'frameworks': ['fastapi', 'react', etc],
                'complexity_score': 0.0-1.0,
                'is_code': bool,
                'is_documentation': bool,
                'suggested_workspace': 'code'|'research'|etc,
                'metadata': {...}
            }
        """
        try:
            analysis = {
                'content_type': 'unknown',
                'file_type': 'unknown',
                'auto_tags': [],
                'language': None,
                'frameworks': [],
                'complexity_score': 0.0,
                'is_code': False,
                'is_documentation': False,
                'suggested_workspace': workspace,
                'metadata': {},
                'confidence': 0.0
            }
            
            # File extension analysis
            if filename:
                file_ext = Path(filename).suffix.lower()
                analysis['metadata']['file_extension'] = file_ext
                
                # Determine content type by extension
                if file_ext in self.image_extensions:
                    analysis['content_type'] = 'image'
                    return await self._analyze_image_content(content, analysis)
                elif file_ext in self.video_extensions:
                    analysis['content_type'] = 'video'
                    analysis['auto_tags'].extend(['video', 'media'])
                    return analysis
                elif file_ext in self.audio_extensions:
                    analysis['content_type'] = 'audio'
                    analysis['auto_tags'].extend(['audio', 'media'])
                    return analysis
                elif file_ext in self.document_extensions:
                    analysis['content_type'] = 'document'
                    analysis['auto_tags'].extend(['document', 'office'])
                    return analysis
            
            # Text content analysis
            if isinstance(content, bytes):
                try:
                    content = content.decode('utf-8')
                except UnicodeDecodeError:
                    content = content.decode('utf-8', errors='replace')
            
            if isinstance(content, str):
                analysis['content_type'] = 'text'
                return await self._analyze_text_content(content, filename, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {
                'content_type': 'unknown',
                'auto_tags': ['error'],
                'suggested_workspace': workspace,
                'error': str(e)
            }
    
    async def _analyze_text_content(self, content: str, filename: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze text content for patterns and features"""
        try:
            content_lower = content.lower()
            lines = content.split('\n')
            
            # Basic metrics
            analysis['metadata'].update({
                'char_count': len(content),
                'line_count': len(lines),
                'word_count': len(content.split()),
                'avg_line_length': sum(len(line) for line in lines) / len(lines) if lines else 0
            })
            
            # Language detection
            detected_languages = []
            for lang, patterns in self.language_patterns.items():
                matches = 0
                for pattern in patterns:
                    matches += len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                
                if matches > 0:
                    detected_languages.append((lang, matches))
            
            # Sort by match count
            detected_languages.sort(key=lambda x: x[1], reverse=True)
            
            if detected_languages:
                analysis['language'] = detected_languages[0][0]
                analysis['is_code'] = True
                analysis['auto_tags'].append(detected_languages[0][0])
                analysis['confidence'] = min(detected_languages[0][1] / 10.0, 1.0)
                
                # Add programming tag
                analysis['auto_tags'].extend(['programming', 'code'])
                
                # Suggest code workspace
                analysis['suggested_workspace'] = 'code'
            
            # Content type detection
            content_types = []
            for content_type, patterns in self.content_patterns.items():
                matches = 0
                for pattern in patterns:
                    matches += len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                    # Also check filename
                    if filename and re.search(pattern, filename, re.IGNORECASE):
                        matches += 5  # Filename matches are weighted higher
                
                if matches > 0:
                    content_types.append((content_type, matches))
            
            # Add content type tags
            content_types.sort(key=lambda x: x[1], reverse=True)
            for content_type, score in content_types[:3]:  # Top 3
                analysis['auto_tags'].append(content_type)
                if content_type in ['documentation', 'research', 'academic', 'tutorial']:
                    analysis['is_documentation'] = True
                    analysis['suggested_workspace'] = 'research'
            
            # Framework detection
            detected_frameworks = []
            for framework, patterns in self.framework_patterns.items():
                matches = 0
                for pattern in patterns:
                    matches += len(re.findall(pattern, content, re.IGNORECASE))
                
                if matches > 0:
                    detected_frameworks.append((framework, matches))
            
            # Add framework tags
            detected_frameworks.sort(key=lambda x: x[1], reverse=True)
            for framework, score in detected_frameworks[:3]:  # Top 3
                analysis['frameworks'].append(framework)
                analysis['auto_tags'].append(framework)
            
            # Complexity score calculation
            complexity_factors = [
                len(re.findall(r'class\s+\w+', content)) * 0.1,  # Classes
                len(re.findall(r'def\s+\w+', content)) * 0.05,   # Functions
                len(re.findall(r'function\s+\w+', content)) * 0.05,  # JS functions
                len(re.findall(r'if\s+', content)) * 0.02,       # Conditionals
                len(re.findall(r'for\s+', content)) * 0.02,      # Loops
                len(re.findall(r'while\s+', content)) * 0.02,    # Loops
                len(re.findall(r'try\s*{', content)) * 0.03,     # Error handling
                len(re.findall(r'except\s+', content)) * 0.03,   # Error handling
            ]
            
            analysis['complexity_score'] = min(sum(complexity_factors), 1.0)
            
            # Add complexity-based tags
            if analysis['complexity_score'] > 0.7:
                analysis['auto_tags'].append('complex')
            elif analysis['complexity_score'] > 0.3:
                analysis['auto_tags'].append('moderate')
            else:
                analysis['auto_tags'].append('simple')
            
            # Special file patterns
            if filename:
                filename_lower = filename.lower()
                
                # Git-related files
                if any(git_file in filename_lower for git_file in ['gitignore', 'gitattributes', 'gitmodules']):
                    analysis['auto_tags'].extend(['git', 'vcs'])
                
                # Config files
                if any(conf_ext in filename_lower for conf_ext in ['.env', '.ini', '.toml', '.yaml', '.yml', 'config']):
                    analysis['auto_tags'].extend(['configuration', 'settings'])
                
                # Documentation files
                if any(doc_file in filename_lower for doc_file in ['readme', 'changelog', 'license', 'contributing']):
                    analysis['auto_tags'].extend(['documentation', 'project'])
                    analysis['is_documentation'] = True
                    analysis['suggested_workspace'] = 'research'
                
                # Test files
                if any(test_pattern in filename_lower for test_pattern in ['test_', '_test.', '.test.', '.spec.']):
                    analysis['auto_tags'].extend(['testing', 'quality'])
            
            # Remove duplicates and sort
            analysis['auto_tags'] = sorted(list(set(analysis['auto_tags'])))
            
            # Final workspace suggestion logic
            if analysis['is_code']:
                analysis['suggested_workspace'] = 'code'
            elif analysis['is_documentation']:
                analysis['suggested_workspace'] = 'research'
            elif any(tag in analysis['auto_tags'] for tag in ['configuration', 'devops', 'pipeline']):
                analysis['suggested_workspace'] = 'projects'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in text analysis: {e}")
            analysis['auto_tags'].append('analysis_error')
            return analysis
    
    async def _analyze_image_content(self, content: Union[str, bytes], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image content (placeholder for future vision model integration)"""
        try:
            analysis['content_type'] = 'image'
            analysis['auto_tags'].extend(['image', 'visual', 'media'])
            
            # Basic image analysis
            if isinstance(content, bytes):
                analysis['metadata']['size_bytes'] = len(content)
                
                # Simple format detection based on magic bytes
                if content.startswith(b'\xFF\xD8\xFF'):
                    analysis['file_type'] = 'jpeg'
                    analysis['auto_tags'].append('jpeg')
                elif content.startswith(b'\x89PNG'):
                    analysis['file_type'] = 'png'
                    analysis['auto_tags'].append('png')
                elif content.startswith(b'GIF8'):
                    analysis['file_type'] = 'gif'
                    analysis['auto_tags'].append('gif')
                elif content.startswith(b'<svg'):
                    analysis['file_type'] = 'svg'
                    analysis['auto_tags'].extend(['svg', 'vector'])
            
            # TODO: Future vision model integration for:
            # - Scene detection
            # - Object recognition  
            # - Text extraction (OCR)
            # - Content categorization
            
            analysis['suggested_workspace'] = 'research'  # Default for images
            analysis['confidence'] = 0.8
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in image analysis: {e}")
            analysis['auto_tags'].append('image_error')
            return analysis
    
    def extract_entities(self, content: str) -> List[str]:
        """Extract potential entities (names, technologies, etc.) from content"""
        try:
            entities = []
            
            # Technology patterns
            tech_patterns = [
                r'\b(?:Python|JavaScript|TypeScript|Java|C\+\+|Rust|Go|SQL)\b',
                r'\b(?:React|Vue|Angular|Django|Flask|FastAPI|Express)\b',
                r'\b(?:Docker|Kubernetes|AWS|Azure|GCP|Jenkins)\b',
                r'\b(?:MongoDB|PostgreSQL|MySQL|Redis|ElasticSearch)\b',
                r'\b(?:Git|GitHub|GitLab|Bitbucket|SVN)\b',
            ]
            
            for pattern in tech_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                entities.extend([match.lower() for match in matches])
            
            # Remove duplicates
            return list(set(entities))
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    async def analyze_multimodal_content(
        self, 
        text_content: str, 
        image_data: bytes, 
        filename: str
    ) -> Dict[str, Any]:
        """Analyze combined text and image content"""
        try:
            # Analyze text part
            text_analysis = await self._analyze_text_content(text_content, filename, {
                'content_type': 'multimodal',
                'auto_tags': ['multimodal'],
                'metadata': {}
            })
            
            # Analyze image part
            image_analysis = await self._analyze_image_content(image_data, {
                'content_type': 'multimodal',
                'auto_tags': ['multimodal'],
                'metadata': {}
            })
            
            # Combine analyses
            combined_analysis = text_analysis.copy()
            combined_analysis['content_type'] = 'multimodal'
            combined_analysis['auto_tags'] = list(set(
                text_analysis.get('auto_tags', []) + 
                image_analysis.get('auto_tags', []) + 
                ['multimodal']
            ))
            
            # Merge metadata
            combined_analysis['metadata'].update(image_analysis.get('metadata', {}))
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"Error in multimodal analysis: {e}")
            return {
                'content_type': 'multimodal',
                'auto_tags': ['multimodal', 'error'],
                'error': str(e)
            }
    
    def suggest_tags_from_workspace_context(self, workspace: str, existing_tags: List[str]) -> List[str]:
        """Suggest additional tags based on workspace context"""
        workspace_suggestions = {
            'code': ['development', 'programming', 'software'],
            'research': ['study', 'analysis', 'knowledge'],
            'projects': ['project', 'work', 'deliverable'],
            'personal': ['personal', 'notes', 'private']
        }
        
        suggestions = workspace_suggestions.get(workspace, [])
        return [tag for tag in suggestions if tag not in existing_tags]