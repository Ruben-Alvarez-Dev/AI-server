"""
Resource Pressure Monitoring System
Continuous monitoring with predictive alerts and trend analysis
"""

import asyncio
import psutil
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import deque
import statistics

from core.logging_config import get_logger

logger = get_logger("resource_monitoring")

@dataclass
class ResourceSnapshot:
    """Single point-in-time resource measurement"""
    timestamp: datetime
    disk_usage_percent: float
    disk_free_gb: float
    ram_usage_percent: float
    ram_free_gb: float
    cpu_usage_percent: float
    load_average: float
    nvme_connected: bool
    active_processes: int
    network_io_kb: float

@dataclass
class ResourceTrend:
    """Resource trend analysis"""
    metric_name: str
    current_value: float
    trend_direction: str  # "increasing", "decreasing", "stable"
    rate_of_change: float  # per hour
    predicted_exhaustion: Optional[datetime]
    confidence_level: float  # 0.0 to 1.0

@dataclass
class Alert:
    """Resource alert"""
    timestamp: datetime
    severity: str  # "info", "warning", "critical", "emergency"
    metric: str
    message: str
    current_value: float
    threshold: float
    predicted_impact: Optional[str] = None

class ResourcePressureMonitor:
    """
    Advanced resource monitoring with predictive capabilities
    """
    
    ALERT_THRESHOLDS = {
        "disk_warning": 75,
        "disk_critical": 85,
        "disk_emergency": 95,
        "ram_warning": 80,
        "ram_critical": 90,
        "ram_emergency": 95,
        "cpu_warning": 75,
        "cpu_critical": 85,
        "cpu_emergency": 95,
        "load_warning": 8.0,
        "load_critical": 12.0,
        "load_emergency": 16.0
    }
    
    TREND_ANALYSIS_WINDOW = 50  # Number of samples for trend analysis
    PREDICTION_HORIZON_HOURS = 24  # How far ahead to predict
    
    def __init__(self, base_path: Path, monitoring_interval: int = 30):
        self.base_path = base_path
        self.monitoring_interval = monitoring_interval
        self.is_monitoring = False
        
        # Data storage
        self.snapshots = deque(maxlen=2000)  # Keep last 2000 snapshots (~16 hours at 30s intervals)
        self.alerts = deque(maxlen=1000)     # Keep last 1000 alerts
        self.alert_callbacks: List[Callable] = []
        
        # Trend analysis
        self.trends: Dict[str, ResourceTrend] = {}
        
        # Performance tracking
        self.monitoring_stats = {
            "samples_collected": 0,
            "alerts_generated": 0,
            "predictions_made": 0,
            "monitoring_start_time": None
        }
    
    async def start_monitoring(self):
        """Start continuous resource monitoring"""
        
        if self.is_monitoring:
            logger.warning("Resource monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitoring_stats["monitoring_start_time"] = datetime.now()
        logger.info("Starting resource pressure monitoring")
        
        try:
            while self.is_monitoring:
                await self._collect_snapshot()
                await self._analyze_trends()
                await self._check_alerts()
                await asyncio.sleep(self.monitoring_interval)
                
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
        finally:
            self.is_monitoring = False
            logger.info("Resource monitoring stopped")
    
    async def stop_monitoring(self):
        """Stop resource monitoring"""
        self.is_monitoring = False
        logger.info("Stopping resource monitoring")
    
    async def _collect_snapshot(self):
        """Collect current resource snapshot"""
        
        try:
            # Disk metrics
            disk_usage = psutil.disk_usage(str(self.base_path))
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            disk_free_gb = disk_usage.free / (1024**3)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            ram_percent = memory.percent
            ram_free_gb = memory.available / (1024**3)
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else cpu_percent / 10
            
            # Process metrics
            active_processes = len(psutil.pids())
            
            # Network metrics (simplified)
            net_io = psutil.net_io_counters()
            network_io_kb = (net_io.bytes_sent + net_io.bytes_recv) / 1024
            
            # NVME detection
            nvme_connected = await self._detect_nvme()
            
            # Create snapshot
            snapshot = ResourceSnapshot(
                timestamp=datetime.now(),
                disk_usage_percent=disk_percent,
                disk_free_gb=disk_free_gb,
                ram_usage_percent=ram_percent,
                ram_free_gb=ram_free_gb,
                cpu_usage_percent=cpu_percent,
                load_average=load_avg,
                nvme_connected=nvme_connected,
                active_processes=active_processes,
                network_io_kb=network_io_kb
            )
            
            # Store snapshot
            self.snapshots.append(snapshot)
            self.monitoring_stats["samples_collected"] += 1
            
            logger.debug(f"Collected resource snapshot: disk={disk_percent:.1f}%, ram={ram_percent:.1f}%, cpu={cpu_percent:.1f}%")
            
        except Exception as e:
            logger.error(f"Error collecting resource snapshot: {e}")
    
    async def _detect_nvme(self) -> bool:
        """Detect NVME connection (simplified version)"""
        try:
            # Check common mount points
            nvme_paths = ["/Volumes/AI-Server-NVME", "/Volumes/Memory-Server", "/Volumes/T7"]
            for path in nvme_paths:
                if Path(path).exists():
                    return True
            return False
        except:
            return False
    
    async def _analyze_trends(self):
        """Analyze resource trends and predict future issues"""
        
        if len(self.snapshots) < 10:  # Need minimum data for analysis
            return
        
        try:
            # Get recent snapshots for trend analysis
            recent_snapshots = list(self.snapshots)[-self.TREND_ANALYSIS_WINDOW:]
            
            # Analyze each metric
            await self._analyze_metric_trend("disk_usage_percent", recent_snapshots)
            await self._analyze_metric_trend("ram_usage_percent", recent_snapshots)
            await self._analyze_metric_trend("cpu_usage_percent", recent_snapshots)
            await self._analyze_metric_trend("load_average", recent_snapshots)
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
    
    async def _analyze_metric_trend(self, metric_name: str, snapshots: List[ResourceSnapshot]):
        """Analyze trend for a specific metric"""
        
        values = [getattr(snapshot, metric_name) for snapshot in snapshots]
        timestamps = [snapshot.timestamp for snapshot in snapshots]
        
        if len(values) < 5:
            return
        
        try:
            # Calculate trend direction and rate
            current_value = values[-1]
            
            # Linear regression for trend
            n = len(values)
            x_values = [(ts - timestamps[0]).total_seconds() / 3600 for ts in timestamps]  # Hours
            y_values = values
            
            # Simple linear regression
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(y_values)
            
            numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                rate_of_change = 0
            else:
                rate_of_change = numerator / denominator  # Change per hour
            
            # Determine trend direction
            if abs(rate_of_change) < 0.1:  # Less than 0.1% change per hour
                trend_direction = "stable"
            elif rate_of_change > 0:
                trend_direction = "increasing"
            else:
                trend_direction = "decreasing"
            
            # Predict exhaustion time (for increasing trends)
            predicted_exhaustion = None
            confidence_level = 0.0
            
            if trend_direction == "increasing" and rate_of_change > 0:
                # Calculate when metric might reach 100%
                time_to_exhaustion_hours = (100 - current_value) / rate_of_change
                
                if 0 < time_to_exhaustion_hours <= self.PREDICTION_HORIZON_HOURS:
                    predicted_exhaustion = datetime.now() + timedelta(hours=time_to_exhaustion_hours)
                    
                    # Confidence based on trend consistency
                    recent_values = values[-min(10, len(values)):]
                    variance = statistics.variance(recent_values) if len(recent_values) > 1 else 0
                    confidence_level = max(0.0, min(1.0, 1.0 - (variance / 100.0)))
            
            # Store trend analysis
            trend = ResourceTrend(
                metric_name=metric_name,
                current_value=current_value,
                trend_direction=trend_direction,
                rate_of_change=rate_of_change,
                predicted_exhaustion=predicted_exhaustion,
                confidence_level=confidence_level
            )
            
            self.trends[metric_name] = trend
            
            if predicted_exhaustion and confidence_level > 0.7:
                self.monitoring_stats["predictions_made"] += 1
                logger.warning(f"Predicted {metric_name} exhaustion at {predicted_exhaustion} (confidence: {confidence_level:.2f})")
            
        except Exception as e:
            logger.error(f"Error analyzing trend for {metric_name}: {e}")
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        
        if not self.snapshots:
            return
        
        current = self.snapshots[-1]
        
        # Check each metric against thresholds
        await self._check_metric_alert("disk", current.disk_usage_percent, "disk_usage_percent")
        await self._check_metric_alert("ram", current.ram_usage_percent, "ram_usage_percent") 
        await self._check_metric_alert("cpu", current.cpu_usage_percent, "cpu_usage_percent")
        await self._check_metric_alert("load", current.load_average, "load_average")
        
        # Check for rapid changes
        await self._check_rapid_change_alerts()
        
        # Check trend-based alerts
        await self._check_trend_alerts()
    
    async def _check_metric_alert(self, metric_type: str, current_value: float, metric_name: str):
        """Check alerts for a specific metric"""
        
        # Determine severity level
        severity = None
        threshold = 0
        
        if current_value >= self.ALERT_THRESHOLDS.get(f"{metric_type}_emergency", 95):
            severity = "emergency"
            threshold = self.ALERT_THRESHOLDS.get(f"{metric_type}_emergency", 95)
        elif current_value >= self.ALERT_THRESHOLDS.get(f"{metric_type}_critical", 90):
            severity = "critical"
            threshold = self.ALERT_THRESHOLDS.get(f"{metric_type}_critical", 90)
        elif current_value >= self.ALERT_THRESHOLDS.get(f"{metric_type}_warning", 75):
            severity = "warning"
            threshold = self.ALERT_THRESHOLDS.get(f"{metric_type}_warning", 75)
        
        if severity:
            # Check if we recently alerted on this (avoid spam)
            recent_alerts = [a for a in self.alerts if 
                           a.metric == metric_name and 
                           a.severity == severity and
                           (datetime.now() - a.timestamp).total_seconds() < 300]  # 5 minutes
            
            if not recent_alerts:
                alert = Alert(
                    timestamp=datetime.now(),
                    severity=severity,
                    metric=metric_name,
                    message=f"{metric_type.upper()} usage is {severity}: {current_value:.1f}%",
                    current_value=current_value,
                    threshold=threshold
                )
                
                await self._fire_alert(alert)
    
    async def _check_rapid_change_alerts(self):
        """Check for rapid resource changes"""
        
        if len(self.snapshots) < 5:
            return
        
        recent_snapshots = list(self.snapshots)[-5:]  # Last 5 samples
        
        for metric_name in ["disk_usage_percent", "ram_usage_percent", "cpu_usage_percent"]:
            values = [getattr(s, metric_name) for s in recent_snapshots]
            
            # Check for rapid increase (>10% in 5 samples)
            change = values[-1] - values[0]
            if change > 10:
                alert = Alert(
                    timestamp=datetime.now(),
                    severity="warning",
                    metric=metric_name,
                    message=f"Rapid increase in {metric_name}: +{change:.1f}% in {len(values)} samples",
                    current_value=values[-1],
                    threshold=values[0] + 10,
                    predicted_impact="Potential resource exhaustion if trend continues"
                )
                
                await self._fire_alert(alert)
    
    async def _check_trend_alerts(self):
        """Check for trend-based alerts"""
        
        for metric_name, trend in self.trends.items():
            if trend.predicted_exhaustion and trend.confidence_level > 0.6:
                time_to_exhaustion = trend.predicted_exhaustion - datetime.now()
                hours_remaining = time_to_exhaustion.total_seconds() / 3600
                
                if hours_remaining <= 2:  # Less than 2 hours
                    severity = "emergency"
                elif hours_remaining <= 6:  # Less than 6 hours
                    severity = "critical"
                elif hours_remaining <= 12:  # Less than 12 hours
                    severity = "warning"
                else:
                    continue
                
                alert = Alert(
                    timestamp=datetime.now(),
                    severity=severity,
                    metric=metric_name,
                    message=f"Predicted resource exhaustion in {hours_remaining:.1f} hours",
                    current_value=trend.current_value,
                    threshold=100.0,
                    predicted_impact=f"Resource will be exhausted at {trend.predicted_exhaustion}"
                )
                
                await self._fire_alert(alert)
    
    async def _fire_alert(self, alert: Alert):
        """Fire an alert and notify subscribers"""
        
        self.alerts.append(alert)
        self.monitoring_stats["alerts_generated"] += 1
        
        # Log alert
        log_func = {
            "info": logger.info,
            "warning": logger.warning, 
            "critical": logger.error,
            "emergency": logger.critical
        }.get(alert.severity, logger.info)
        
        log_func(f"ALERT [{alert.severity.upper()}] {alert.message}")
        
        # Notify callbacks
        for callback in self.alert_callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def register_alert_callback(self, callback: Callable):
        """Register callback for alert notifications"""
        self.alert_callbacks.append(callback)
        logger.info("Alert callback registered")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        
        if not self.snapshots:
            return {"status": "no_data", "is_monitoring": self.is_monitoring}
        
        current = self.snapshots[-1]
        
        return {
            "status": "active" if self.is_monitoring else "stopped",
            "is_monitoring": self.is_monitoring,
            "last_snapshot": asdict(current),
            "snapshot_count": len(self.snapshots),
            "recent_alerts": len([a for a in self.alerts if (datetime.now() - a.timestamp).total_seconds() < 3600]),
            "monitoring_stats": self.monitoring_stats.copy()
        }
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """Get current trend analysis"""
        
        return {
            "trends": {name: asdict(trend) for name, trend in self.trends.items()},
            "analysis_window": self.TREND_ANALYSIS_WINDOW,
            "prediction_horizon_hours": self.PREDICTION_HORIZON_HOURS
        }
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get alert history for specified hours"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alerts if a.timestamp > cutoff_time]
        
        return [asdict(alert) for alert in recent_alerts]
    
    def get_resource_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get resource history for specified hours"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [s for s in self.snapshots if s.timestamp > cutoff_time]
        
        return [asdict(snapshot) for snapshot in recent_snapshots]
    
    async def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "monitoring_status": self.get_current_status(),
            "trends": self.get_trend_analysis(),
            "recent_alerts": self.get_alert_history(24),
            "resource_summary": {},
            "predictions": {},
            "recommendations": []
        }
        
        # Resource summary
        if self.snapshots:
            recent = list(self.snapshots)[-min(100, len(self.snapshots)):]
            
            for metric in ["disk_usage_percent", "ram_usage_percent", "cpu_usage_percent"]:
                values = [getattr(s, metric) for s in recent]
                report["resource_summary"][metric] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "std_dev": statistics.stdev(values) if len(values) > 1 else 0
                }
        
        # Predictions
        for metric_name, trend in self.trends.items():
            if trend.predicted_exhaustion and trend.confidence_level > 0.5:
                report["predictions"][metric_name] = {
                    "predicted_exhaustion": trend.predicted_exhaustion.isoformat(),
                    "confidence_level": trend.confidence_level,
                    "rate_of_change": trend.rate_of_change
                }
        
        # Recommendations
        recommendations = []
        
        if self.snapshots:
            current = self.snapshots[-1]
            
            if current.disk_usage_percent > 80:
                recommendations.append("Consider enabling aggressive cleanup or adding external storage")
            
            if current.ram_usage_percent > 85:
                recommendations.append("High memory usage detected - consider reducing buffer sizes")
            
            if current.cpu_usage_percent > 80:
                recommendations.append("High CPU usage - consider reducing processing intensity")
            
            if not current.nvme_connected and current.disk_usage_percent > 70:
                recommendations.append("External NVME not detected - consider connecting for additional storage")
        
        report["recommendations"] = recommendations
        
        return report