"""
Workspace Manager for Memory-Server
Handles workspace creation, management, and organization
"""

import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.config import get_config
from core.logging_config import get_logger

logger = get_logger("workspace-manager")
config = get_config()

class WorkspaceManager:
    """Manages workspaces for organizing documents and content"""
    
    def __init__(self):
        self.workspaces_dir = config.DATA_DIR / "workspaces"
        self.workspaces_dir.mkdir(parents=True, exist_ok=True)
        
        # Default workspaces
        self.default_workspaces = {
            "code": {
                "description": "Development work, code files, commits, and IDE activity",
                "tags": ["development", "programming", "code"],
                "auto_tags": ["git", "vscode", "commit"],
                "file_patterns": ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx", "*.html", "*.css", "*.md"]
            },
            "research": {
                "description": "Research materials, documentation, papers, and web content",
                "tags": ["research", "documentation", "learning"],
                "auto_tags": ["web", "pdf", "docs"],
                "file_patterns": ["*.md", "*.pdf", "*.txt", "*.docx"]
            },
            "projects": {
                "description": "Project-specific content and documentation",
                "tags": ["projects", "work", "client"],
                "auto_tags": ["project", "deliverable"],
                "file_patterns": ["*"]
            },
            "personal": {
                "description": "Personal notes, ideas, and miscellaneous content",
                "tags": ["personal", "notes", "ideas"],
                "auto_tags": ["note", "idea", "personal"],
                "file_patterns": ["*.md", "*.txt"]
            }
        }
        
        # Initialize default workspaces
        asyncio.create_task(self._initialize_default_workspaces())
        
        self.active_workspace = "research"  # Default active workspace
    
    async def _initialize_default_workspaces(self):
        """Initialize default workspaces if they don't exist"""
        try:
            for workspace_name, workspace_config in self.default_workspaces.items():
                await self.create_workspace(
                    workspace_name, 
                    workspace_config["description"],
                    workspace_config,
                    skip_if_exists=True
                )
        except Exception as e:
            logger.error(f"Error initializing default workspaces: {e}")
    
    async def create_workspace(
        self, 
        name: str, 
        description: str = "",
        config_data: Optional[Dict[str, Any]] = None,
        skip_if_exists: bool = False
    ):
        """Create a new workspace"""
        try:
            workspace_dir = self.workspaces_dir / name
            
            if workspace_dir.exists():
                if skip_if_exists:
                    return
                else:
                    raise ValueError(f"Workspace '{name}' already exists")
            
            # Create workspace directory structure
            workspace_dir.mkdir(parents=True, exist_ok=True)
            (workspace_dir / "documents").mkdir(exist_ok=True)
            (workspace_dir / "chunks").mkdir(exist_ok=True)
            (workspace_dir / "summaries").mkdir(exist_ok=True)
            (workspace_dir / "metadata").mkdir(exist_ok=True)
            
            # Create workspace configuration
            workspace_config = {
                "name": name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "document_count": 0,
                "last_updated": datetime.now().isoformat(),
                "tags": config_data.get("tags", []) if config_data else [],
                "auto_tags": config_data.get("auto_tags", []) if config_data else [],
                "file_patterns": config_data.get("file_patterns", ["*"]) if config_data else ["*"],
                "settings": {
                    "auto_summarize": True,
                    "auto_tag": True,
                    "chunking_strategy": "late_chunking",
                    "max_chunk_size": config.DEFAULT_CHUNK_SIZE,
                    "chunk_overlap": config.CHUNK_OVERLAP
                }
            }
            
            # Save workspace config
            config_file = workspace_dir / "workspace.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(workspace_config, f, indent=2)
            
            logger.info(f"Created workspace: {name}")
            
        except Exception as e:
            logger.error(f"Error creating workspace {name}: {e}")
            raise
    
    async def list_workspaces(self) -> List[str]:
        """List all available workspaces"""
        try:
            workspaces = []
            
            for item in self.workspaces_dir.iterdir():
                if item.is_dir() and (item / "workspace.json").exists():
                    workspaces.append(item.name)
            
            # Sort alphabetically
            return sorted(workspaces)
            
        except Exception as e:
            logger.error(f"Error listing workspaces: {e}")
            return []
    
    async def get_workspace_config(self, name: str) -> Dict[str, Any]:
        """Get workspace configuration"""
        try:
            workspace_dir = self.workspaces_dir / name
            config_file = workspace_dir / "workspace.json"
            
            if not config_file.exists():
                raise ValueError(f"Workspace '{name}' not found")
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error getting config for workspace {name}: {e}")
            raise
    
    async def update_workspace_config(self, name: str, updates: Dict[str, Any]):
        """Update workspace configuration"""
        try:
            config_data = await self.get_workspace_config(name)
            config_data.update(updates)
            config_data["last_updated"] = datetime.now().isoformat()
            
            workspace_dir = self.workspaces_dir / name
            config_file = workspace_dir / "workspace.json"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
                
            logger.debug(f"Updated config for workspace {name}")
            
        except Exception as e:
            logger.error(f"Error updating config for workspace {name}: {e}")
            raise
    
    async def get_document_count(self, name: str) -> int:
        """Get number of documents in workspace"""
        try:
            workspace_dir = self.workspaces_dir / name / "documents"
            
            if not workspace_dir.exists():
                return 0
            
            # Count .txt files (actual documents)
            count = len(list(workspace_dir.glob("*.txt")))
            return count
            
        except Exception as e:
            logger.error(f"Error getting document count for workspace {name}: {e}")
            return 0
    
    async def get_workspace_stats(self, name: str) -> Dict[str, Any]:
        """Get detailed workspace statistics"""
        try:
            config_data = await self.get_workspace_config(name)
            doc_count = await self.get_document_count(name)
            
            # Count chunks
            chunks_dir = self.workspaces_dir / name / "chunks"
            chunk_count = len(list(chunks_dir.glob("*.json"))) if chunks_dir.exists() else 0
            
            # Get directory sizes
            workspace_dir = self.workspaces_dir / name
            total_size = sum(f.stat().st_size for f in workspace_dir.rglob('*') if f.is_file())
            
            # Recent activity
            recent_docs = []
            docs_dir = workspace_dir / "documents"
            if docs_dir.exists():
                metadata_files = list(docs_dir.glob("*.metadata.json"))
                # Sort by creation time and take last 5
                metadata_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                for metadata_file in metadata_files[:5]:
                    try:
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            recent_docs.append({
                                "document_id": metadata.get("document_id", "unknown"),
                                "filename": metadata.get("original_filename", "unknown"),
                                "created_at": metadata.get("created_at", "unknown")
                            })
                    except Exception:
                        continue
            
            return {
                "name": name,
                "description": config_data.get("description", ""),
                "created_at": config_data.get("created_at", ""),
                "last_updated": config_data.get("last_updated", ""),
                "document_count": doc_count,
                "chunk_count": chunk_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "tags": config_data.get("tags", []),
                "recent_documents": recent_docs,
                "settings": config_data.get("settings", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting stats for workspace {name}: {e}")
            return {}
    
    async def delete_workspace(self, name: str, confirm: bool = False):
        """Delete a workspace and all its content"""
        try:
            if not confirm:
                raise ValueError("Workspace deletion requires confirmation")
            
            if name in self.default_workspaces:
                raise ValueError(f"Cannot delete default workspace '{name}'")
            
            workspace_dir = self.workspaces_dir / name
            
            if not workspace_dir.exists():
                raise ValueError(f"Workspace '{name}' not found")
            
            # Remove directory and all contents
            import shutil
            shutil.rmtree(workspace_dir)
            
            logger.info(f"Deleted workspace: {name}")
            
        except Exception as e:
            logger.error(f"Error deleting workspace {name}: {e}")
            raise
    
    def get_active_workspace(self) -> str:
        """Get the currently active workspace"""
        return self.active_workspace
    
    def set_active_workspace(self, name: str):
        """Set the active workspace"""
        self.active_workspace = name
        logger.debug(f"Active workspace set to: {name}")
    
    async def suggest_workspace(self, filename: str, content: str = "") -> str:
        """Suggest appropriate workspace based on file characteristics"""
        try:
            filename_lower = filename.lower()
            
            # Code files
            code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.java', '.cpp', '.c', '.h'}
            if any(filename_lower.endswith(ext) for ext in code_extensions):
                return "code"
            
            # Documentation and research
            doc_extensions = {'.md', '.txt', '.pdf', '.docx'}
            if any(filename_lower.endswith(ext) for ext in doc_extensions):
                # Check content for code-related keywords
                if content:
                    code_keywords = ['function', 'class', 'import', 'def ', 'var ', 'const ', 'let ', 'git', 'commit']
                    if any(keyword in content.lower() for keyword in code_keywords):
                        return "code"
                
                return "research"
            
            # Project files
            project_files = {'readme', 'changelog', 'license', 'makefile', 'dockerfile'}
            if any(keyword in filename_lower for keyword in project_files):
                return "projects"
            
            # Default to research
            return "research"
            
        except Exception as e:
            logger.error(f"Error suggesting workspace for {filename}: {e}")
            return "research"
    
    async def get_workspace_summary(self, name: str) -> str:
        """Generate a summary of workspace contents"""
        try:
            stats = await self.get_workspace_stats(name)
            
            summary = f"Workspace '{name}':\n"
            summary += f"- {stats['document_count']} documents\n"
            summary += f"- {stats['chunk_count']} chunks\n"
            summary += f"- {stats['total_size_mb']} MB total size\n"
            
            if stats['recent_documents']:
                summary += f"- Recent documents: {', '.join([doc['filename'] for doc in stats['recent_documents'][:3]])}\n"
            
            if stats['tags']:
                summary += f"- Tags: {', '.join(stats['tags'])}\n"
                
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for workspace {name}: {e}")
            return f"Workspace '{name}' - Error generating summary"

