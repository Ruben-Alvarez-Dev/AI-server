"""
Document Processor for Memory-Server
Handles document processing, chunking, embedding, and storage
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import json
import uuid

from core.config import get_config
from core.logging_config import get_logger
from .content_analyzer import ContentAnalyzer
from .summarization_service import SummarizationService

logger = get_logger("document-processor")
config = get_config()

class DocumentProcessor:
    """Processes documents for ingestion into Memory-Server"""
    
    def __init__(self):
        self.supported_extensions = {
            '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
            '.json', '.yaml', '.yml', '.xml', '.csv', '.sql', '.sh', '.bash',
            '.c', '.cpp', '.h', '.hpp', '.java', '.php', '.rb', '.go', '.rs',
            '.scala', '.swift', '.kt', '.dart', '.vue', '.svelte', '.astro',
            '.dockerfile', '.gitignore', '.env', '.toml', '.ini', '.cfg',
            # Add image and document extensions
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff',
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx'
        }
        
        # Initialize content analyzer and summarization service
        self.content_analyzer = ContentAnalyzer()
        self.summarization_service = SummarizationService()
        
        # Statistics
        self.stats = {
            "documents_processed": 0,
            "total_chunks_created": 0,
            "total_processing_time": 0.0,
            "errors": 0,
            "last_processed": None
        }
    
    async def process_file(
        self,
        file_path: str,
        original_name: str,
        workspace: str = "research",
        auto_summarize: bool = True,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Process a single file and return document ID
        
        Args:
            file_path: Path to the file to process
            original_name: Original filename
            workspace: Workspace to store in
            auto_summarize: Whether to generate automatic summary
            tags: Optional tags to add
            
        Returns:
            Document ID
        """
        start_time = datetime.now()
        
        try:
            file_path = Path(file_path)
            
            # Validate file
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Check file extension
            file_extension = file_path.suffix.lower()
            if file_extension not in self.supported_extensions:
                logger.warning(f"Unsupported file type: {file_extension}")
                # Still process as text
            
            # Read file content (handle both text and binary)
            content, is_binary = await self._read_file_content_smart(file_path)
            if not content and not is_binary:
                raise ValueError("File is empty or contains only whitespace")
            
            # Analyze content for intelligent tagging
            content_analysis = await self.content_analyzer.analyze_content(
                content=content,
                filename=original_name,
                file_path=str(file_path),
                workspace=workspace
            )
            
            # Use suggested workspace if none provided or if auto-suggestion is better
            if content_analysis.get('suggested_workspace') and content_analysis.get('confidence', 0) > 0.7:
                workspace = content_analysis['suggested_workspace']
            
            # Merge auto-tags with manual tags
            auto_tags = content_analysis.get('auto_tags', [])
            combined_tags = list(set((tags or []) + auto_tags))
            
            # Generate document ID
            content_str = content if isinstance(content, str) else f"binary_file_{original_name}"
            document_id = self._generate_document_id(content_str, original_name)
            
            # Create document metadata with content analysis
            metadata = {
                "document_id": document_id,
                "original_filename": original_name,
                "file_path": str(file_path),
                "workspace": workspace,
                "file_extension": file_extension,
                "file_size": file_path.stat().st_size,
                "content_hash": self._generate_content_hash(content_str),
                "created_at": datetime.now().isoformat(),
                "tags": combined_tags,
                "manual_tags": tags or [],
                "auto_tags": auto_tags,
                "auto_summarize": auto_summarize,
                "processing_status": "processing",
                # Content analysis results
                "content_analysis": {
                    "content_type": content_analysis.get('content_type', 'unknown'),
                    "file_type": content_analysis.get('file_type', 'unknown'),
                    "language": content_analysis.get('language'),
                    "frameworks": content_analysis.get('frameworks', []),
                    "complexity_score": content_analysis.get('complexity_score', 0.0),
                    "is_code": content_analysis.get('is_code', False),
                    "is_documentation": content_analysis.get('is_documentation', False),
                    "confidence": content_analysis.get('confidence', 0.0),
                    "analysis_metadata": content_analysis.get('metadata', {})
                },
                "is_binary": is_binary
            }
            
            # Add MIME type
            mime_type, _ = mimetypes.guess_type(str(file_path))
            metadata["mime_type"] = mime_type or "text/plain"
            
            # Store raw document
            await self._store_document(document_id, content, metadata, workspace)
            
            # Process for late chunking (if enabled)
            if config.USE_LATE_CHUNKING:
                await self._process_late_chunking(document_id, content, metadata)
            else:
                await self._process_traditional_chunking(document_id, content, metadata)
            
            # Generate summary if requested
            if auto_summarize:
                await self._generate_document_summary(document_id, content, metadata)
            
            # Update metadata status
            metadata["processing_status"] = "completed"
            metadata["processed_at"] = datetime.now().isoformat()
            await self._update_document_metadata(document_id, metadata, workspace)
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_stats(processing_time, success=True)
            
            logger.info(f"Document processed successfully: {original_name} -> {document_id}")
            return document_id
            
        except Exception as e:
            await self._update_stats(0, success=False)
            logger.error(f"Error processing file {original_name}: {e}")
            raise
    
    async def process_web_content(
        self,
        content: str,
        url: str,
        workspace: str = "research",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process web-scraped content"""
        try:
            # Generate document ID
            document_id = self._generate_document_id(content, url)
            
            # Create metadata
            doc_metadata = {
                "document_id": document_id,
                "source_url": url,
                "workspace": workspace,
                "content_type": "web_scraped",
                "content_hash": self._generate_content_hash(content),
                "created_at": datetime.now().isoformat(),
                "processing_status": "processing"
            }
            
            # Add additional metadata
            if metadata:
                doc_metadata.update(metadata)
            
            # Store and process
            await self._store_document(document_id, content, doc_metadata, workspace)
            
            if config.USE_LATE_CHUNKING:
                await self._process_late_chunking(document_id, content, doc_metadata)
            else:
                await self._process_traditional_chunking(document_id, content, doc_metadata)
            
            # Analyze content for better summarization
            content_analysis = await self.content_analyzer.analyze_content(
                content=content,
                filename=url.split('/')[-1] if url else 'web_content',
                file_path=url,
                workspace=workspace
            )
            doc_metadata['content_analysis'] = content_analysis
            
            # Generate summary
            await self._generate_document_summary(document_id, content, doc_metadata)
            
            # Update status
            doc_metadata["processing_status"] = "completed"
            doc_metadata["processed_at"] = datetime.now().isoformat()
            await self._update_document_metadata(document_id, doc_metadata, workspace)
            
            logger.info(f"Web content processed: {url} -> {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing web content from {url}: {e}")
            raise
    
    async def _read_file_content(self, file_path: Path) -> str:
        """Read and decode file content (legacy method)"""
        content, _ = await self._read_file_content_smart(file_path)
        return content if isinstance(content, str) else ""
    
    async def _read_file_content_smart(self, file_path: Path) -> tuple[Union[str, bytes], bool]:
        """
        Smart file content reader that handles both text and binary files
        
        Returns:
            (content, is_binary): content as str/bytes and boolean indicating if binary
        """
        try:
            file_ext = file_path.suffix.lower()
            
            # Image and binary file extensions
            binary_extensions = {
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.ico',
                '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
                '.zip', '.tar', '.gz', '.7z', '.rar',
                '.mp4', '.avi', '.mkv', '.mov', '.mp3', '.wav', '.flac'
            }
            
            # For binary files, read as bytes
            if file_ext in binary_extensions:
                with open(file_path, 'rb') as f:
                    content = f.read()
                return content, True
            
            # For text files, try different encodings
            try:
                # Try UTF-8 first
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content, False
            except UnicodeDecodeError:
                try:
                    # Try latin-1 as fallback
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                    return content, False
                except Exception:
                    # Final fallback - read as binary and decode with errors
                    with open(file_path, 'rb') as f:
                        binary_content = f.read()
                        text_content = binary_content.decode('utf-8', errors='replace')
                    return text_content, False
                    
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    def _generate_document_id(self, content: str, identifier: str) -> str:
        """Generate unique document ID"""
        # Use content hash + identifier for uniqueness
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        identifier_hash = hashlib.sha256(identifier.encode()).hexdigest()[:8]
        return f"doc_{content_hash}_{identifier_hash}"
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate content hash for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _store_document(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any],
        workspace: str
    ):
        """Store document in workspace directory"""
        try:
            # Create workspace directory
            workspace_dir = config.DATA_DIR / "workspaces" / workspace / "documents"
            workspace_dir.mkdir(parents=True, exist_ok=True)
            
            # Store document content
            doc_file = workspace_dir / f"{document_id}.txt"
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Store metadata
            metadata_file = workspace_dir / f"{document_id}.metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.debug(f"Document stored: {document_id} in workspace {workspace}")
            
        except Exception as e:
            logger.error(f"Error storing document {document_id}: {e}")
            raise
    
    async def _update_document_metadata(
        self, 
        document_id: str, 
        metadata: Dict[str, Any],
        workspace: str
    ):
        """Update document metadata"""
        try:
            workspace_dir = config.DATA_DIR / "workspaces" / workspace / "documents"
            metadata_file = workspace_dir / f"{document_id}.metadata.json"
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
                
        except Exception as e:
            logger.error(f"Error updating metadata for {document_id}: {e}")
            raise
    
    async def _process_late_chunking(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ):
        """Process document using late chunking approach"""
        try:
            # This will integrate with the late chunking engine once it's ready
            # For now, create a placeholder chunk structure
            
            chunks_dir = config.DATA_DIR / "workspaces" / metadata["workspace"] / "chunks"
            chunks_dir.mkdir(parents=True, exist_ok=True)
            
            # Simple chunking for now
            chunk_size = config.DEFAULT_CHUNK_SIZE
            overlap = int(chunk_size * config.CHUNK_OVERLAP)
            
            chunks = []
            start = 0
            chunk_id = 0
            
            while start < len(content):
                end = min(start + chunk_size, len(content))
                chunk_content = content[start:end]
                
                if chunk_content.strip():
                    chunk_data = {
                        "chunk_id": f"{document_id}_chunk_{chunk_id}",
                        "document_id": document_id,
                        "content": chunk_content,
                        "start_idx": start,
                        "end_idx": end,
                        "chunk_size": len(chunk_content),
                        "created_at": datetime.now().isoformat()
                    }
                    
                    chunks.append(chunk_data)
                    
                    # Store chunk
                    chunk_file = chunks_dir / f"{chunk_data['chunk_id']}.json"
                    with open(chunk_file, 'w', encoding='utf-8') as f:
                        json.dump(chunk_data, f, indent=2)
                    
                    chunk_id += 1
                
                start = end - overlap
                if start >= len(content):
                    break
            
            # Update metadata with chunk info
            metadata["chunks_created"] = len(chunks)
            metadata["chunking_method"] = "late_chunking_placeholder"
            
            logger.debug(f"Created {len(chunks)} chunks for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error in late chunking for {document_id}: {e}")
            raise
    
    async def _process_traditional_chunking(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ):
        """Process document using traditional chunking"""
        # Similar to late chunking but with different metadata
        await self._process_late_chunking(document_id, content, metadata)
        metadata["chunking_method"] = "traditional_chunking"
    
    async def _generate_document_summary(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ):
        """Generate automatic document summary using advanced LLM-powered service"""
        try:
            # Determine optimal summary type based on content analysis
            content_analysis = metadata.get('content_analysis', {})
            is_code = content_analysis.get('is_code', False)
            is_documentation = content_analysis.get('is_documentation', False)
            content_type = content_analysis.get('content_type', 'unknown')
            
            # Choose summary type based on content
            if is_code:
                summary_type = 'technical'
            elif is_documentation:
                summary_type = 'structured'  
            elif content_type in ['academic', 'research']:
                summary_type = 'abstractive'
            else:
                summary_type = 'extractive'  # Default fallback
            
            # Generate summary using advanced service
            summary_result = await self.summarization_service.summarize_content(
                content=content,
                summary_type=summary_type,
                metadata={
                    'document_id': document_id,
                    'filename': metadata.get('original_filename', ''),
                    'workspace': metadata.get('workspace', 'research'),
                    'content_analysis': content_analysis
                }
            )
            
            # Store comprehensive summary data
            metadata["auto_summary"] = summary_result['summary']
            metadata["summary_type"] = summary_result['summary_type']
            metadata["summary_confidence"] = summary_result['confidence']
            metadata["summary_model_used"] = summary_result['model_used']
            metadata["summary_generated_at"] = datetime.now().isoformat()
            metadata["summary_metadata"] = summary_result.get('metadata', {})
            
            # Store alternative summaries if generated
            if summary_result.get('alternatives'):
                metadata["summary_alternatives"] = summary_result['alternatives']
            
            logger.info(f"Generated {summary_type} summary for document {document_id} "
                       f"(confidence: {summary_result['confidence']:.2f})")
            
        except Exception as e:
            logger.error(f"Advanced summarization failed for {document_id}: {e}")
            # Fallback to simple extractive summary
            await self._generate_fallback_summary(document_id, content, metadata)
    
    async def _generate_fallback_summary(
        self, 
        document_id: str, 
        content: str, 
        metadata: Dict[str, Any]
    ):
        """Generate simple fallback summary when advanced summarization fails"""
        try:
            lines = content.split('\n')
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            
            # Take first few meaningful lines as summary
            summary_lines = non_empty_lines[:5]
            summary = ' '.join(summary_lines)
            
            # Truncate if too long
            if len(summary) > 500:
                summary = summary[:497] + "..."
            
            metadata["auto_summary"] = summary
            metadata["summary_type"] = "extractive_fallback"
            metadata["summary_confidence"] = 0.3  # Low confidence for fallback
            metadata["summary_generated_at"] = datetime.now().isoformat()
            
            logger.warning(f"Used fallback summary for document {document_id}")
            
        except Exception as e:
            logger.error(f"Even fallback summary failed for {document_id}: {e}")
            metadata["auto_summary"] = "Summary generation failed"
            metadata["summary_type"] = "error"
    
    async def delete_document(self, workspace: str, document_id: str):
        """Delete a document and its associated data"""
        try:
            workspace_dir = config.DATA_DIR / "workspaces" / workspace
            
            # Delete document files
            doc_file = workspace_dir / "documents" / f"{document_id}.txt"
            metadata_file = workspace_dir / "documents" / f"{document_id}.metadata.json"
            
            if doc_file.exists():
                doc_file.unlink()
            if metadata_file.exists():
                metadata_file.unlink()
            
            # Delete chunks
            chunks_dir = workspace_dir / "chunks"
            if chunks_dir.exists():
                for chunk_file in chunks_dir.glob(f"{document_id}_chunk_*.json"):
                    chunk_file.unlink()
            
            logger.info(f"Document deleted: {document_id} from workspace {workspace}")
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    async def _update_stats(self, processing_time: float, success: bool = True):
        """Update processing statistics"""
        if success:
            self.stats["documents_processed"] += 1
            self.stats["total_processing_time"] += processing_time
            self.stats["last_processed"] = datetime.now().isoformat()
        else:
            self.stats["errors"] += 1
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.stats.copy()
        
        if stats["documents_processed"] > 0:
            stats["avg_processing_time"] = stats["total_processing_time"] / stats["documents_processed"]
        else:
            stats["avg_processing_time"] = 0.0
            
        return stats