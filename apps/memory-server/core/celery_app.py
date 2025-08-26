"""
Celery Configuration for Memory-Server
Async task processing with Redis broker
"""

import os
from celery import Celery
from pathlib import Path

# Create Celery instance
celery_app = Celery(
    'memory_server',
    broker=os.getenv('REDIS_URL', 'redis://localhost:8801/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:8801/1'),
    include=[
        'workers.document_worker',
        'workers.embedding_worker',
        'workers.simple_document_worker'
    ]
)

# Configuration
celery_app.conf.update(
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Time settings
    timezone='UTC',
    enable_utc=True,
    
    # Task execution limits
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Warning at 4 minutes
    
    # Worker configuration
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (memory management)
    worker_pool_restarts=True,
    
    # Task behavior
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Requeue tasks if worker dies
    task_compression='gzip',  # Compress large task payloads
    
    # Result backend configuration
    result_expires=3600,  # Results expire after 1 hour
    result_compression='gzip',
    
    # Queue configuration
    task_default_queue='default',
    task_queues={
        'default': {'routing_key': 'default'},
        'documents': {'routing_key': 'documents'},
        'embeddings': {'routing_key': 'embeddings'},
        'priority': {'routing_key': 'priority'},
    },
    
    # Rate limiting (optional)
    task_default_rate_limit='100/m',  # 100 tasks per minute default
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# Beat schedule for periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    'cleanup-temp-files': {
        'task': 'workers.maintenance.cleanup_temp_files',
        'schedule': 3600.0,  # Every hour
    },
    'update-statistics': {
        'task': 'workers.maintenance.update_statistics',
        'schedule': 300.0,  # Every 5 minutes
    },
}

# Task routing
celery_app.conf.task_routes = {
    'workers.document_worker.*': {'queue': 'documents'},
    'workers.embedding_worker.*': {'queue': 'embeddings'},
    'workers.maintenance.*': {'queue': 'default'},
}

print("✅ Celery configured with Redis broker at redis://localhost:8801 (Flower: 8811)")