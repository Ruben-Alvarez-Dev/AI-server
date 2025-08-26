"""
Progress Router - Real-time Transparent Progress Tracking
Provides Cline/Claude Code style visibility into AI Orchestra operations
"""

import asyncio
import logging
import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
import uuid

logger = logging.getLogger(__name__)

# WebSocket connection manager
class ProgressConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_sessions: Dict[str, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_sessions[client_id] = {
            'websocket': websocket,
            'connected_at': datetime.now(),
            'active_tasks': []
        }
        logger.info(f"Client {client_id} connected for progress tracking")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if client_id in self.client_sessions:
            del self.client_sessions[client_id]
        logger.info(f"Client {client_id} disconnected")
    
    async def broadcast_progress(self, message: Dict[str, Any]):
        """Broadcast progress update to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send progress update to specific client"""
        if client_id in self.client_sessions:
            try:
                websocket = self.client_sessions[client_id]['websocket']
                await websocket.send_text(json.dumps(message))
            except:
                self.disconnect(self.client_sessions[client_id]['websocket'], client_id)

# Global progress manager
progress_manager = ProgressConnectionManager()

# Progress tracking data structures
class ProgressStep:
    def __init__(self, step_id: str, title: str, description: str, agent: str = "system"):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.agent = agent
        self.status = "pending"  # pending, in_progress, completed, failed
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.substeps: List['ProgressStep'] = []
        self.metadata: Dict[str, Any] = {}
        self.progress_percentage = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'title': self.title,
            'description': self.description,
            'agent': self.agent,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            'substeps': [step.to_dict() for step in self.substeps],
            'metadata': self.metadata,
            'progress_percentage': self.progress_percentage
        }

class TaskProgress:
    def __init__(self, task_id: str, title: str, description: str):
        self.task_id = task_id
        self.title = title
        self.description = description
        self.created_at = datetime.now()
        self.status = "initializing"
        self.steps: List[ProgressStep] = []
        self.current_step_index = -1
        self.overall_progress = 0
        self.estimated_completion: Optional[datetime] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_step(self, step: ProgressStep):
        self.steps.append(step)
        return step
    
    def start_step(self, step_id: str) -> bool:
        for i, step in enumerate(self.steps):
            if step.step_id == step_id:
                step.status = "in_progress"
                step.start_time = datetime.now()
                self.current_step_index = i
                self.update_overall_progress()
                return True
        return False
    
    def complete_step(self, step_id: str, metadata: Dict[str, Any] = None) -> bool:
        for step in self.steps:
            if step.step_id == step_id:
                step.status = "completed"
                step.end_time = datetime.now()
                step.progress_percentage = 100
                if metadata:
                    step.metadata.update(metadata)
                self.update_overall_progress()
                return True
        return False
    
    def fail_step(self, step_id: str, error_message: str) -> bool:
        for step in self.steps:
            if step.step_id == step_id:
                step.status = "failed"
                step.end_time = datetime.now()
                step.metadata['error'] = error_message
                self.update_overall_progress()
                return True
        return False
    
    def update_step_progress(self, step_id: str, progress: int, message: str = "") -> bool:
        for step in self.steps:
            if step.step_id == step_id:
                step.progress_percentage = min(100, max(0, progress))
                if message:
                    step.metadata['current_message'] = message
                self.update_overall_progress()
                return True
        return False
    
    def update_overall_progress(self):
        if not self.steps:
            self.overall_progress = 0
            return
        
        completed_steps = sum(1 for step in self.steps if step.status == "completed")
        in_progress_steps = [step for step in self.steps if step.status == "in_progress"]
        
        # Calculate progress
        base_progress = (completed_steps / len(self.steps)) * 100
        
        # Add partial progress from current step
        if in_progress_steps:
            current_step_progress = in_progress_steps[0].progress_percentage
            base_progress += (current_step_progress / len(self.steps))
        
        self.overall_progress = min(100, base_progress)
        
        # Update status
        if completed_steps == len(self.steps):
            self.status = "completed"
        elif any(step.status == "failed" for step in self.steps):
            self.status = "failed"
        elif any(step.status == "in_progress" for step in self.steps):
            self.status = "in_progress"
        else:
            self.status = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'steps': [step.to_dict() for step in self.steps],
            'current_step_index': self.current_step_index,
            'overall_progress': self.overall_progress,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'metadata': self.metadata
        }

# Global task tracking
active_tasks: Dict[str, TaskProgress] = {}

# API Router
router = APIRouter()

class ProgressTracker:
    """
    Transparent Progress Tracker for AI Orchestra
    Provides real-time visibility into all AI agent activities
    """
    
    @staticmethod
    async def start_task(
        title: str, 
        description: str, 
        steps: List[Dict[str, str]] = None,
        client_id: str = None
    ) -> str:
        """Start tracking a new task"""
        task_id = str(uuid.uuid4())[:12]
        
        task_progress = TaskProgress(
            task_id=task_id,
            title=title,
            description=description
        )
        
        # Add predefined steps
        if steps:
            for step_info in steps:
                step = ProgressStep(
                    step_id=str(uuid.uuid4())[:8],
                    title=step_info['title'],
                    description=step_info['description'],
                    agent=step_info.get('agent', 'system')
                )
                task_progress.add_step(step)
        
        active_tasks[task_id] = task_progress
        
        # Broadcast to all connected clients
        await progress_manager.broadcast_progress({
            'type': 'task_started',
            'task': task_progress.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"Started tracking task: {task_id} - {title}")
        return task_id
    
    @staticmethod
    async def add_step(
        task_id: str, 
        title: str, 
        description: str, 
        agent: str = "system"
    ) -> str:
        """Add a new step to an existing task"""
        if task_id not in active_tasks:
            return ""
        
        step_id = str(uuid.uuid4())[:8]
        step = ProgressStep(
            step_id=step_id,
            title=title,
            description=description,
            agent=agent
        )
        
        active_tasks[task_id].add_step(step)
        
        # Broadcast update
        await progress_manager.broadcast_progress({
            'type': 'step_added',
            'task_id': task_id,
            'step': step.to_dict(),
            'timestamp': datetime.now().isoformat()
        })
        
        return step_id
    
    @staticmethod
    async def start_step(task_id: str, step_id: str, message: str = ""):
        """Start executing a step"""
        if task_id in active_tasks:
            if active_tasks[task_id].start_step(step_id):
                await progress_manager.broadcast_progress({
                    'type': 'step_started',
                    'task_id': task_id,
                    'step_id': step_id,
                    'message': message,
                    'task': active_tasks[task_id].to_dict(),
                    'timestamp': datetime.now().isoformat()
                })
    
    @staticmethod
    async def update_step(task_id: str, step_id: str, progress: int, message: str = ""):
        """Update step progress"""
        if task_id in active_tasks:
            if active_tasks[task_id].update_step_progress(step_id, progress, message):
                await progress_manager.broadcast_progress({
                    'type': 'step_updated',
                    'task_id': task_id,
                    'step_id': step_id,
                    'progress': progress,
                    'message': message,
                    'task': active_tasks[task_id].to_dict(),
                    'timestamp': datetime.now().isoformat()
                })
    
    @staticmethod
    async def complete_step(
        task_id: str, 
        step_id: str, 
        message: str = "", 
        metadata: Dict[str, Any] = None
    ):
        """Complete a step"""
        if task_id in active_tasks:
            completion_metadata = metadata or {}
            if message:
                completion_metadata['completion_message'] = message
            
            if active_tasks[task_id].complete_step(step_id, completion_metadata):
                await progress_manager.broadcast_progress({
                    'type': 'step_completed',
                    'task_id': task_id,
                    'step_id': step_id,
                    'message': message,
                    'metadata': completion_metadata,
                    'task': active_tasks[task_id].to_dict(),
                    'timestamp': datetime.now().isoformat()
                })
    
    @staticmethod
    async def fail_step(task_id: str, step_id: str, error_message: str):
        """Mark a step as failed"""
        if task_id in active_tasks:
            if active_tasks[task_id].fail_step(step_id, error_message):
                await progress_manager.broadcast_progress({
                    'type': 'step_failed',
                    'task_id': task_id,
                    'step_id': step_id,
                    'error': error_message,
                    'task': active_tasks[task_id].to_dict(),
                    'timestamp': datetime.now().isoformat()
                })
    
    @staticmethod
    async def complete_task(task_id: str, summary: str = "", metadata: Dict[str, Any] = None):
        """Complete an entire task"""
        if task_id in active_tasks:
            task = active_tasks[task_id]
            task.status = "completed"
            task.metadata.update(metadata or {})
            if summary:
                task.metadata['completion_summary'] = summary
            
            await progress_manager.broadcast_progress({
                'type': 'task_completed',
                'task_id': task_id,
                'summary': summary,
                'task': task.to_dict(),
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Completed task: {task_id}")

# API Endpoints

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await progress_manager.connect(websocket, client_id)
    try:
        while True:
            # Keep connection alive and handle any client messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client commands
            if message.get('type') == 'get_active_tasks':
                response = {
                    'type': 'active_tasks',
                    'tasks': [task.to_dict() for task in active_tasks.values()],
                    'timestamp': datetime.now().isoformat()
                }
                await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        progress_manager.disconnect(websocket, client_id)

@router.get("/dashboard")
async def get_progress_dashboard():
    """Serve the progress dashboard HTML"""
    return HTMLResponse(content=PROGRESS_DASHBOARD_HTML, status_code=200)

@router.get("/active-tasks")
async def get_active_tasks():
    """Get all currently active tasks"""
    return {
        'active_tasks': [task.to_dict() for task in active_tasks.values()],
        'total_active': len(active_tasks),
        'timestamp': datetime.now().isoformat()
    }

@router.get("/task/{task_id}")
async def get_task_details(task_id: str):
    """Get details of a specific task"""
    if task_id in active_tasks:
        return active_tasks[task_id].to_dict()
    return {'error': 'Task not found'}, 404

@router.post("/demo-task")
async def create_demo_task():
    """Create a demo task for testing the progress interface"""
    
    demo_steps = [
        {'title': 'Analyzing requirements', 'description': 'Breaking down user requirements', 'agent': 'architect'},
        {'title': 'Planning implementation', 'description': 'Creating detailed implementation plan', 'agent': 'task_planner'},
        {'title': 'Frontend development', 'description': 'Implementing user interface', 'agent': 'alpha_frontend'},
        {'title': 'Backend development', 'description': 'Creating API endpoints', 'agent': 'beta_backend'},
        {'title': 'Testing code', 'description': 'Running comprehensive test suite', 'agent': 'tdd_verifier'},
        {'title': 'Code review', 'description': 'Peer review and quality check', 'agent': 'qa_checker'},
        {'title': 'Deployment', 'description': 'Deploying to production environment', 'agent': 'gamma_systems'}
    ]
    
    task_id = await ProgressTracker.start_task(
        title="Demo Development Task",
        description="A demonstration of the AI Orchestra development workflow",
        steps=demo_steps
    )
    
    # Simulate step progression
    asyncio.create_task(_simulate_demo_progress(task_id))
    
    return {'task_id': task_id, 'message': 'Demo task started'}

async def _simulate_demo_progress(task_id: str):
    """Simulate demo task progression"""
    await asyncio.sleep(1)
    
    task = active_tasks.get(task_id)
    if not task:
        return
    
    for i, step in enumerate(task.steps):
        await ProgressTracker.start_step(task_id, step.step_id, f"Starting {step.title.lower()}...")
        
        # Simulate progress updates
        for progress in [25, 50, 75, 100]:
            await asyncio.sleep(0.5)
            message = f"{step.title} - {progress}% complete"
            if progress == 100:
                message = f"✅ {step.title} completed successfully"
            
            if progress < 100:
                await ProgressTracker.update_step(task_id, step.step_id, progress, message)
            else:
                await ProgressTracker.complete_step(
                    task_id, 
                    step.step_id, 
                    message,
                    {'lines_of_code': 150 + i * 25, 'tests_passed': 12 + i * 3}
                )
    
    await ProgressTracker.complete_task(
        task_id, 
        "🎉 Demo task completed successfully! All components are working together.",
        {'total_lines': 750, 'total_tests': 42, 'quality_score': 0.95}
    )

# Progress Dashboard HTML
PROGRESS_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Orchestra - Progress Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            line-height: 1.6;
        }
        
        .header {
            background: #161b22;
            padding: 1rem 2rem;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: between;
            align-items: center;
        }
        
        .logo {
            font-size: 1.5rem;
            font-weight: bold;
            color: #58a6ff;
        }
        
        .status {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #238636;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .main-content {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .task-container {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }
        
        .task-header {
            padding: 1rem 1.5rem;
            background: #21262d;
            border-bottom: 1px solid #30363d;
            display: flex;
            justify-content: between;
            align-items: center;
        }
        
        .task-title {
            font-size: 1.2rem;
            font-weight: 600;
            color: #f0f6fc;
        }
        
        .task-status {
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
        }
        
        .status-in-progress { background: #1f6feb20; color: #58a6ff; }
        .status-completed { background: #23863620; color: #3fb950; }
        .status-failed { background: #da363320; color: #f85149; }
        .status-pending { background: #f8514920; color: #ff7b72; }
        
        .task-progress {
            padding: 0 1.5rem 1rem;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #21262d;
            border-radius: 4px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #1f6feb, #58a6ff);
            transition: width 0.3s ease;
            border-radius: 4px;
        }
        
        .steps-list {
            list-style: none;
        }
        
        .step-item {
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #30363d;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        
        .step-item:last-child {
            border-bottom: none;
        }
        
        .step-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: bold;
        }
        
        .icon-pending { background: #f8514920; color: #ff7b72; }
        .icon-in-progress { 
            background: #1f6feb20; 
            color: #58a6ff; 
            animation: spin 1s linear infinite; 
        }
        .icon-completed { background: #23863620; color: #3fb950; }
        .icon-failed { background: #da363320; color: #f85149; }
        
        @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        
        .step-content {
            flex: 1;
        }
        
        .step-title {
            font-weight: 600;
            color: #f0f6fc;
            margin-bottom: 0.25rem;
        }
        
        .step-description {
            color: #8b949e;
            font-size: 0.9rem;
        }
        
        .step-agent {
            background: #30363d;
            color: #c9d1d9;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }
        
        .step-meta {
            display: flex;
            align-items: center;
            gap: 1rem;
            font-size: 0.8rem;
            color: #8b949e;
        }
        
        .no-tasks {
            text-align: center;
            padding: 4rem 2rem;
            color: #8b949e;
        }
        
        .connection-status {
            position: fixed;
            top: 1rem;
            right: 1rem;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 500;
        }
        
        .connected { background: #23863620; color: #3fb950; }
        .disconnected { background: #da363320; color: #f85149; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">🎭 AI Orchestra</div>
        <div class="status">
            <div class="status-indicator"></div>
            <span>Active</span>
        </div>
    </div>
    
    <div class="connection-status" id="connectionStatus">
        Connecting...
    </div>
    
    <div class="main-content">
        <div id="tasksContainer">
            <div class="no-tasks">
                <h3>No active tasks</h3>
                <p>AI Orchestra is ready to begin work</p>
            </div>
        </div>
    </div>
    
    <script>
        class ProgressDashboard {
            constructor() {
                this.socket = null;
                this.tasks = new Map();
                this.connect();
            }
            
            connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const clientId = 'dashboard_' + Date.now();
                this.socket = new WebSocket(`${protocol}//${window.location.host}/progress/ws/${clientId}`);
                
                this.socket.onopen = () => {
                    this.updateConnectionStatus(true);
                    this.requestActiveTasks();
                };
                
                this.socket.onclose = () => {
                    this.updateConnectionStatus(false);
                    setTimeout(() => this.connect(), 3000);
                };
                
                this.socket.onmessage = (event) => {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                };
            }
            
            updateConnectionStatus(connected) {
                const status = document.getElementById('connectionStatus');
                status.textContent = connected ? 'Connected' : 'Disconnected';
                status.className = `connection-status ${connected ? 'connected' : 'disconnected'}`;
            }
            
            requestActiveTasks() {
                if (this.socket.readyState === WebSocket.OPEN) {
                    this.socket.send(JSON.stringify({ type: 'get_active_tasks' }));
                }
            }
            
            handleMessage(message) {
                switch (message.type) {
                    case 'task_started':
                        this.addTask(message.task);
                        break;
                    case 'active_tasks':
                        message.tasks.forEach(task => this.addTask(task));
                        break;
                    case 'step_started':
                    case 'step_updated':
                    case 'step_completed':
                    case 'step_failed':
                        this.updateTask(message.task);
                        break;
                    case 'task_completed':
                        this.updateTask(message.task);
                        break;
                }
            }
            
            addTask(task) {
                this.tasks.set(task.task_id, task);
                this.renderTasks();
            }
            
            updateTask(task) {
                this.tasks.set(task.task_id, task);
                this.renderTasks();
            }
            
            renderTasks() {
                const container = document.getElementById('tasksContainer');
                
                if (this.tasks.size === 0) {
                    container.innerHTML = `
                        <div class="no-tasks">
                            <h3>No active tasks</h3>
                            <p>AI Orchestra is ready to begin work</p>
                        </div>
                    `;
                    return;
                }
                
                const tasksHtml = Array.from(this.tasks.values())
                    .map(task => this.renderTask(task))
                    .join('');
                
                container.innerHTML = tasksHtml;
            }
            
            renderTask(task) {
                const statusClass = `status-${task.status.replace('_', '-')}`;
                const progressWidth = Math.round(task.overall_progress);
                
                const stepsHtml = task.steps
                    .map(step => this.renderStep(step))
                    .join('');
                
                return `
                    <div class="task-container">
                        <div class="task-header">
                            <div>
                                <div class="task-title">${task.title}</div>
                                <div class="task-description">${task.description}</div>
                            </div>
                            <div class="task-status ${statusClass}">
                                ${task.status.replace('_', ' ')}
                            </div>
                        </div>
                        <div class="task-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${progressWidth}%"></div>
                            </div>
                            <div class="progress-text">${progressWidth}% complete</div>
                        </div>
                        <ul class="steps-list">
                            ${stepsHtml}
                        </ul>
                    </div>
                `;
            }
            
            renderStep(step) {
                const iconClass = `icon-${step.status.replace('_', '-')}`;
                const iconText = this.getStepIcon(step.status);
                const duration = step.duration ? `${step.duration.toFixed(1)}s` : '';
                const currentMessage = step.metadata?.current_message || step.metadata?.completion_message || '';
                
                return `
                    <li class="step-item">
                        <div class="step-icon ${iconClass}">${iconText}</div>
                        <div class="step-content">
                            <div class="step-title">${step.title}</div>
                            <div class="step-description">${step.description}</div>
                            ${currentMessage ? `<div class="step-message">${currentMessage}</div>` : ''}
                            <div class="step-meta">
                                <span class="step-agent">${step.agent}</span>
                                ${duration ? `<span>${duration}</span>` : ''}
                                ${step.progress_percentage > 0 ? `<span>${step.progress_percentage}%</span>` : ''}
                            </div>
                        </div>
                    </li>
                `;
            }
            
            getStepIcon(status) {
                const icons = {
                    pending: '○',
                    in_progress: '⟳',
                    completed: '✓',
                    failed: '✗'
                };
                return icons[status] || '○';
            }
        }
        
        // Initialize dashboard
        new ProgressDashboard();
    </script>
</body>
</html>
"""

# Export
__all__ = ['router', 'ProgressTracker', 'TaskProgress', 'ProgressStep']