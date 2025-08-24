"""
Agent Manager - Centralized management of all AI agents
Handles agent lifecycle, health monitoring, and load balancing
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime, timedelta

from ...agents import (
    get_router_agent,
    get_architect_agent,
    get_primary_coder_agent,
    get_secondary_coder_agent,
    get_qa_checker_agent,
    get_debugger_agent,
    AGENT_REGISTRY
)


logger = logging.getLogger(__name__)


class AgentManager:
    """Manages all AI agents and their lifecycle"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.agent_stats: Dict[str, Dict[str, Any]] = {}
        self.model_paths: Dict[str, str] = {}
        self.health_check_interval = 300  # 5 minutes
        self.health_check_task: Optional[asyncio.Task] = None
        self._initialized = False
        self._shutdown = False
    
    async def initialize(self, model_paths: Dict[str, str]):
        """Initialize all agents with their model paths"""
        if self._initialized:
            logger.warning("Agent manager already initialized")
            return
        
        logger.info("Initializing Agent Manager...")
        self.model_paths = model_paths.copy()
        
        # Validate model paths exist
        missing_models = []
        for agent_type, model_path in model_paths.items():
            if not Path(model_path).exists():
                missing_models.append(f"{agent_type}: {model_path}")
        
        if missing_models:
            logger.warning(f"Missing model files: {missing_models}")
            logger.warning("Some agents may fail to initialize")
        
        # Initialize agents
        initialization_tasks = []
        
        for agent_type, model_path in model_paths.items():
            if agent_type in AGENT_REGISTRY:
                task = self._initialize_agent(agent_type, model_path)
                initialization_tasks.append(task)
            else:
                logger.error(f"Unknown agent type: {agent_type}")
        
        # Wait for all agents to initialize
        if initialization_tasks:
            results = await asyncio.gather(*initialization_tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                agent_type = list(model_paths.keys())[i]
                
                if isinstance(result, Exception):
                    logger.error(f"Failed to initialize {agent_type}: {result}")
                    self.agent_stats[agent_type] = {
                        "status": "failed",
                        "error": str(result),
                        "last_updated": datetime.now(),
                        "initialization_time": None
                    }
                else:
                    logger.info(f"Successfully initialized {agent_type}")
                    self.agents[agent_type] = result
                    self.agent_stats[agent_type] = {
                        "status": "healthy",
                        "error": None,
                        "last_updated": datetime.now(),
                        "initialization_time": datetime.now(),
                        "requests_handled": 0,
                        "total_response_time": 0.0,
                        "average_response_time": 0.0
                    }
        
        # Start health monitoring
        await self._start_health_monitoring()
        
        self._initialized = True
        logger.info(f"Agent Manager initialized with {len(self.agents)} agents")
    
    async def _initialize_agent(self, agent_type: str, model_path: str) -> Any:
        """Initialize a single agent"""
        logger.info(f"Initializing {agent_type} agent with model: {model_path}")
        
        try:
            # Get the appropriate factory function
            factory_map = {
                "router": get_router_agent,
                "architect": get_architect_agent,
                "coder_primary": get_primary_coder_agent,
                "coder_secondary": get_secondary_coder_agent,
                "qa_checker": get_qa_checker_agent,
                "debugger": get_debugger_agent
            }
            
            if agent_type not in factory_map:
                raise ValueError(f"No factory function for agent type: {agent_type}")
            
            factory = factory_map[agent_type]
            agent = await factory(model_path)
            
            return agent
            
        except Exception as e:
            logger.error(f"Failed to initialize {agent_type} agent: {e}")
            raise
    
    async def _start_health_monitoring(self):
        """Start background health monitoring task"""
        if self.health_check_task and not self.health_check_task.done():
            return
        
        self.health_check_task = asyncio.create_task(self._health_monitoring_loop())
        logger.info("Started agent health monitoring")
    
    async def _health_monitoring_loop(self):
        """Background loop for agent health monitoring"""
        while not self._shutdown:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def _perform_health_checks(self):
        """Perform health checks on all agents"""
        if not self.agents:
            return
        
        logger.debug("Performing agent health checks")
        
        # Create health check tasks
        health_tasks = []
        agent_types = []
        
        for agent_type, agent in self.agents.items():
            if hasattr(agent, 'health_check'):
                health_tasks.append(agent.health_check())
                agent_types.append(agent_type)
        
        if not health_tasks:
            return
        
        # Execute health checks
        results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            agent_type = agent_types[i]
            
            if isinstance(result, Exception):
                logger.warning(f"Health check failed for {agent_type}: {result}")
                self.agent_stats[agent_type].update({
                    "status": "unhealthy",
                    "error": str(result),
                    "last_updated": datetime.now()
                })
            else:
                health_status = result.get("status", "unknown")
                
                if health_status == "healthy":
                    self.agent_stats[agent_type].update({
                        "status": "healthy",
                        "error": None,
                        "last_updated": datetime.now()
                    })
                else:
                    logger.warning(f"Agent {agent_type} reports unhealthy status: {result}")
                    self.agent_stats[agent_type].update({
                        "status": "unhealthy",
                        "error": result.get("reason", "Unknown health issue"),
                        "last_updated": datetime.now()
                    })
    
    async def get_agent(self, agent_type: str) -> Any:
        """Get a specific agent instance"""
        if not self._initialized:
            raise RuntimeError("Agent manager not initialized")
        
        if agent_type not in self.agents:
            raise ValueError(f"Agent type '{agent_type}' not available")
        
        agent = self.agents[agent_type]
        
        # Update usage stats
        if agent_type in self.agent_stats:
            self.agent_stats[agent_type]["requests_handled"] += 1
        
        return agent
    
    async def get_agents_registry(self) -> Dict[str, Any]:
        """Get registry of all available agents"""
        return self.agents.copy()
    
    async def get_agent_status(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Get status of specific agent or all agents"""
        if agent_type:
            if agent_type not in self.agent_stats:
                raise ValueError(f"Agent type '{agent_type}' not found")
            
            return {
                "agent_type": agent_type,
                "model_path": self.model_paths.get(agent_type),
                **self.agent_stats[agent_type]
            }
        else:
            # Return status of all agents
            return {
                agent_type: {
                    "agent_type": agent_type,
                    "model_path": self.model_paths.get(agent_type),
                    **stats
                }
                for agent_type, stats in self.agent_stats.items()
            }
    
    async def update_agent_stats(self, agent_type: str, response_time: float):
        """Update agent performance statistics"""
        if agent_type not in self.agent_stats:
            return
        
        stats = self.agent_stats[agent_type]
        stats["total_response_time"] += response_time
        
        # Calculate running average
        requests = stats.get("requests_handled", 1)
        stats["average_response_time"] = stats["total_response_time"] / max(1, requests)
        stats["last_updated"] = datetime.now()
    
    async def restart_agent(self, agent_type: str) -> bool:
        """Restart a specific agent"""
        if agent_type not in self.model_paths:
            raise ValueError(f"Agent type '{agent_type}' not configured")
        
        logger.info(f"Restarting agent: {agent_type}")
        
        try:
            # Remove old agent
            if agent_type in self.agents:
                old_agent = self.agents[agent_type]
                if hasattr(old_agent, 'cleanup'):
                    try:
                        await old_agent.cleanup()
                    except Exception as e:
                        logger.warning(f"Error cleaning up old agent: {e}")
                
                del self.agents[agent_type]
            
            # Initialize new agent
            model_path = self.model_paths[agent_type]
            new_agent = await self._initialize_agent(agent_type, model_path)
            
            self.agents[agent_type] = new_agent
            self.agent_stats[agent_type] = {
                "status": "healthy",
                "error": None,
                "last_updated": datetime.now(),
                "initialization_time": datetime.now(),
                "requests_handled": 0,
                "total_response_time": 0.0,
                "average_response_time": 0.0
            }
            
            logger.info(f"Successfully restarted agent: {agent_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restart agent {agent_type}: {e}")
            
            # Mark as failed
            self.agent_stats[agent_type] = {
                "status": "failed",
                "error": str(e),
                "last_updated": datetime.now(),
                "initialization_time": None
            }
            
            return False
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        healthy_agents = len([
            stats for stats in self.agent_stats.values()
            if stats.get("status") == "healthy"
        ])
        
        total_requests = sum(
            stats.get("requests_handled", 0)
            for stats in self.agent_stats.values()
        )
        
        avg_response_time = 0.0
        if self.agent_stats:
            response_times = [
                stats.get("average_response_time", 0)
                for stats in self.agent_stats.values()
                if stats.get("average_response_time", 0) > 0
            ]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "total_agents": len(self.agent_stats),
            "healthy_agents": healthy_agents,
            "failed_agents": len(self.agent_stats) - healthy_agents,
            "health_percentage": (healthy_agents / max(1, len(self.agent_stats))) * 100,
            "total_requests_handled": total_requests,
            "average_response_time": avg_response_time,
            "uptime": (datetime.now() - min(
                stats.get("initialization_time", datetime.now())
                for stats in self.agent_stats.values()
                if stats.get("initialization_time")
            )).total_seconds() if any(
                stats.get("initialization_time") for stats in self.agent_stats.values()
            ) else 0,
            "last_health_check": max(
                stats.get("last_updated", datetime.min)
                for stats in self.agent_stats.values()
            ) if self.agent_stats else None
        }
    
    async def shutdown(self):
        """Shutdown agent manager and cleanup resources"""
        if self._shutdown:
            return
        
        logger.info("Shutting down Agent Manager...")
        self._shutdown = True
        
        # Cancel health monitoring
        if self.health_check_task and not self.health_check_task.done():
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup agents
        cleanup_tasks = []
        for agent_type, agent in self.agents.items():
            if hasattr(agent, 'cleanup'):
                cleanup_tasks.append(agent.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.agents.clear()
        self.agent_stats.clear()
        
        logger.info("Agent Manager shutdown complete")