"""
Code Preprocessor
Specialized preprocessing for code syntax, functions, and programming concepts
Optimized for programming language understanding and code structure
"""

import re
import ast
import logging
from typing import Dict, Any, List, Union, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("embedding-hub.code")

@dataclass
class CodeContext:
    """Context information for code processing"""
    language: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    variables: List[str]
    comments: List[str]
    complexity_score: float

class CodePreprocessor:
    """
    Preprocessor specialized for code embedding generation
    
    Key principles:
    1. Preserve code structure and syntax
    2. Extract semantic information (functions, classes, etc.)
    3. Handle different programming languages appropriately
    4. Maintain relationship between code elements
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.preprocessing_options = config.get('preprocessing', {}).get('options', {})
        
        # Configuration flags
        self.preserve_indentation = self.preprocessing_options.get('preserve_indentation', True)
        self.extract_ast = self.preprocessing_options.get('extract_ast_features', True)
        self.normalize_variables = self.preprocessing_options.get('normalize_variable_names', False)
        self.include_comments = self.preprocessing_options.get('include_comments', True)
        self.language_detection = self.preprocessing_options.get('language_detection', True)
        self.supported_languages = self.preprocessing_options.get('supported_languages', [
            'python', 'javascript', 'typescript', 'go', 'rust', 'java'
        ])
        
        # Language-specific patterns
        self._init_language_patterns()
        
        logger.info(f"Initialized Code preprocessor for languages: {self.supported_languages}")
    
    def _init_language_patterns(self):
        """Initialize language-specific regex patterns"""
        
        self.language_patterns = {
            'python': {
                'functions': r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'classes': r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'imports': r'(?:from\s+[\w.]+\s+)?import\s+([\w.,\s*]+)',
                'comments': r'#.*$',
                'docstrings': r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\''
            },
            'javascript': {
                'functions': r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\(',
                'classes': r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                'imports': r'import\s+.*?from\s+["\']([^"\']+)["\']|import\s+["\']([^"\']+)["\']',
                'comments': r'//.*$|/\*[\s\S]*?\*/',
                'arrow_functions': r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\([^)]*\)\s*=>'
            },
            'typescript': {
                'functions': r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(|([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*\([^)]*\)\s*=>',
                'classes': r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                'imports': r'import\s+.*?from\s+["\']([^"\']+)["\']',
                'interfaces': r'interface\s+([a-zA-Z_$][a-zA-Z0-9_$]*)',
                'types': r'type\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*='
            },
            'go': {
                'functions': r'func\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'structs': r'type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+struct',
                'imports': r'import\s+["\']([^"\']+)["\']',
                'comments': r'//.*$|/\*[\s\S]*?\*/'
            },
            'rust': {
                'functions': r'fn\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'structs': r'struct\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'imports': r'use\s+([\w:]+)',
                'traits': r'trait\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            },
            'java': {
                'functions': r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                'classes': r'(?:public|private)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                'imports': r'import\s+([\w.]+)',
                'interfaces': r'interface\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            }
        }
    
    async def preprocess(self, content: Union[str, bytes], metadata: Dict[str, Any]) -> str:
        """
        Preprocess code content for embedding generation
        
        Args:
            content: Raw code content
            metadata: Additional context (file extension, language hint, etc.)
            
        Returns:
            Preprocessed code optimized for embedding
        """
        try:
            # Convert to string if needed
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            
            # Detect programming language
            language = self._detect_language(content, metadata)
            
            # Analyze code structure
            context = self._analyze_code_structure(content, language)
            
            # Apply preprocessing steps
            processed_content = content
            
            if self.preserve_indentation:
                processed_content = self._normalize_indentation(processed_content, language)
            
            if not self.include_comments:
                processed_content = self._remove_comments(processed_content, language)
            
            if self.normalize_variables and language == 'python':
                processed_content = self._normalize_variable_names(processed_content)
            
            # Add semantic context for embedding
            processed_content = self._add_semantic_context(processed_content, context, metadata)
            
            logger.debug(f"Code preprocessing completed - Language: {language}, Length: {len(processed_content)}")
            
            return processed_content
            
        except Exception as e:
            logger.error(f"Error in code preprocessing: {e}")
            return content  # Fallback to original content
    
    def _detect_language(self, content: str, metadata: Dict[str, Any]) -> str:
        """Detect programming language from content and metadata"""
        
        # Check metadata for language hints
        if 'language' in metadata:
            return metadata['language'].lower()
        
        if 'file_extension' in metadata:
            ext_map = {
                '.py': 'python',
                '.js': 'javascript', 
                '.ts': 'typescript',
                '.go': 'go',
                '.rs': 'rust',
                '.java': 'java',
                '.cpp': 'cpp',
                '.c': 'c',
                '.rb': 'ruby',
                '.php': 'php'
            }
            ext = metadata['file_extension'].lower()
            if ext in ext_map:
                return ext_map[ext]
        
        # Pattern-based detection
        language_scores = {}
        
        for lang, patterns in self.language_patterns.items():
            score = 0
            for pattern_type, pattern in patterns.items():
                matches = len(re.findall(pattern, content, re.MULTILINE))
                score += matches
            language_scores[lang] = score
        
        # Return language with highest score
        if language_scores:
            detected = max(language_scores, key=language_scores.get)
            if language_scores[detected] > 0:
                return detected
        
        return 'unknown'
    
    def _analyze_code_structure(self, content: str, language: str) -> CodeContext:
        """Analyze code structure to extract semantic information"""
        
        functions = []
        classes = []
        imports = []
        variables = []
        comments = []
        
        if language in self.language_patterns:
            patterns = self.language_patterns[language]
            
            # Extract functions
            if 'functions' in patterns:
                func_matches = re.findall(patterns['functions'], content, re.MULTILINE)
                functions = [match for match in func_matches if match]
            
            # Extract classes/structs
            for class_key in ['classes', 'structs']:
                if class_key in patterns:
                    class_matches = re.findall(patterns[class_key], content, re.MULTILINE)
                    classes.extend([match for match in class_matches if match])
            
            # Extract imports
            if 'imports' in patterns:
                import_matches = re.findall(patterns['imports'], content, re.MULTILINE)
                imports = [match for match in import_matches if match]
            
            # Extract comments
            if 'comments' in patterns:
                comment_matches = re.findall(patterns['comments'], content, re.MULTILINE)
                comments = comment_matches
        
        # Calculate complexity score
        complexity = self._calculate_complexity(content)
        
        return CodeContext(
            language=language,
            functions=functions,
            classes=classes,
            imports=imports,
            variables=variables,
            comments=comments,
            complexity_score=complexity
        )
    
    def _calculate_complexity(self, content: str) -> float:
        """Calculate code complexity score"""
        
        complexity_indicators = [
            (r'if\s+', 1.0),      # Conditional statements
            (r'for\s+', 1.5),     # Loops
            (r'while\s+', 1.5),   # Loops
            (r'try\s*:', 2.0),    # Exception handling
            (r'catch\s*\(', 2.0), # Exception handling
            (r'def\s+', 0.5),     # Functions
            (r'class\s+', 0.5),   # Classes
            (r'switch\s*\(', 2.0) # Switch statements
        ]
        
        total_score = 0
        for pattern, weight in complexity_indicators:
            matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
            total_score += matches * weight
        
        # Normalize by content length
        normalized_score = total_score / max(len(content.split('\n')), 1)
        
        return min(normalized_score, 10.0)  # Cap at 10.0
    
    def _normalize_indentation(self, content: str, language: str) -> str:
        """Normalize indentation while preserving structure"""
        
        if language == 'python':
            # Python: convert tabs to 4 spaces
            content = content.expandtabs(4)
        elif language in ['javascript', 'typescript', 'java']:
            # JS/TS/Java: convert tabs to 2 spaces  
            content = content.expandtabs(2)
        
        # Remove excessive blank lines but preserve structure
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content
    
    def _remove_comments(self, content: str, language: str) -> str:
        """Remove comments from code while preserving structure"""
        
        if language in self.language_patterns:
            patterns = self.language_patterns[language]
            
            if 'comments' in patterns:
                content = re.sub(patterns['comments'], '', content, flags=re.MULTILINE)
            
            # Remove docstrings for Python
            if language == 'python' and 'docstrings' in patterns:
                content = re.sub(patterns['docstrings'], '', content, flags=re.MULTILINE)
        
        # Clean up excessive whitespace left by comment removal
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        
        return content
    
    def _normalize_variable_names(self, content: str) -> str:
        """Normalize variable names to reduce vocabulary size (experimental)"""
        
        # This is experimental - normalize common variable patterns
        normalizations = [
            (r'\b[a-z]+_[a-z]+_[a-z]+\b', 'var_compound'),  # snake_case compounds
            (r'\b[a-z]+Temp\b', 'temp_var'),                 # temp variables
            (r'\b[a-z]+Count\b', 'count_var'),               # count variables
            (r'\b[a-z]+Index\b', 'index_var'),               # index variables
        ]
        
        for pattern, replacement in normalizations:
            content = re.sub(pattern, replacement, content)
        
        return content
    
    def _add_semantic_context(self, content: str, context: CodeContext, metadata: Dict[str, Any]) -> str:
        """Add semantic context information for better embeddings"""
        
        # Create context header
        context_header = [
            f"[CODE_CONTEXT]",
            f"Language: {context.language}",
            f"Functions: {len(context.functions)}",
            f"Classes: {len(context.classes)}",
            f"Imports: {len(context.imports)}",
            f"Complexity: {context.complexity_score:.2f}"
        ]
        
        # Add function signatures if not too many
        if len(context.functions) <= 10:
            context_header.append(f"Function_Names: {', '.join(context.functions[:10])}")
        
        # Add class names if not too many
        if len(context.classes) <= 5:
            context_header.append(f"Class_Names: {', '.join(context.classes[:5])}")
        
        # Add key imports
        if len(context.imports) <= 8:
            context_header.append(f"Key_Imports: {', '.join(context.imports[:8])}")
        
        # Add metadata if available
        if metadata:
            if 'file_path' in metadata:
                file_path = Path(metadata['file_path'])
                context_header.append(f"File: {file_path.name}")
            
            if 'purpose' in metadata:
                context_header.append(f"Purpose: {metadata['purpose']}")
        
        context_header.append("[/CODE_CONTEXT]")
        
        # Combine context with content
        full_content = "\n".join(context_header) + "\n\n" + content
        
        return full_content
    
    def extract_code_features(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured features from code for advanced processing
        This can be used by downstream systems for specialized code understanding
        """
        
        language = self._detect_language(content, metadata)
        context = self._analyze_code_structure(content, language)
        
        features = {
            "language": context.language,
            "structure": {
                "function_count": len(context.functions),
                "class_count": len(context.classes),
                "import_count": len(context.imports),
                "complexity_score": context.complexity_score
            },
            "entities": {
                "functions": context.functions[:20],  # Limit for size
                "classes": context.classes[:10],
                "imports": context.imports[:15]
            },
            "metrics": {
                "lines_of_code": len(content.split('\n')),
                "character_count": len(content),
                "avg_line_length": len(content) / max(len(content.split('\n')), 1)
            }
        }
        
        # Add language-specific features
        if language == 'python':
            features["python_specific"] = self._extract_python_features(content)
        elif language in ['javascript', 'typescript']:
            features["js_specific"] = self._extract_js_features(content)
        
        return features
    
    def _extract_python_features(self, content: str) -> Dict[str, Any]:
        """Extract Python-specific features"""
        
        features = {
            "decorators": len(re.findall(r'@\w+', content)),
            "list_comprehensions": len(re.findall(r'\[.*for.*in.*\]', content)),
            "lambda_functions": len(re.findall(r'lambda\s+.*:', content)),
            "async_functions": len(re.findall(r'async\s+def', content)),
            "type_hints": len(re.findall(r':\s*\w+', content))
        }
        
        return features
    
    def _extract_js_features(self, content: str) -> Dict[str, Any]:
        """Extract JavaScript/TypeScript-specific features"""
        
        features = {
            "arrow_functions": len(re.findall(r'=>', content)),
            "async_functions": len(re.findall(r'async\s+', content)),
            "promises": len(re.findall(r'\.then\(|\.catch\(|Promise\.', content)),
            "destructuring": len(re.findall(r'\{.*\}\s*=', content)),
            "template_literals": len(re.findall(r'`.*`', content))
        }
        
        return features