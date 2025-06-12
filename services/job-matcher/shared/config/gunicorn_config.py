import multiprocessing
import os
import sys
from datetime import datetime

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv('WORKER_CLASS', 'sync')
worker_connections = 1000
timeout = int(os.getenv('WORKER_TIMEOUT', '120'))
keepalive = 2

# Restart workers after this many requests, with some variability
max_requests = 1000
max_requests_jitter = 50

# Process naming
proc_name = os.getenv('SERVICE_NAME', 'microservice')

# Logging
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# StatsD integration (for production metrics)
if os.getenv('STATSD_HOST'):
    statsd_host = f"{os.getenv('STATSD_HOST')}:{os.getenv('STATSD_PORT', '8125')}"
    statsd_prefix = f"microservices.{proc_name}"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (for production)
keyfile = os.getenv('SSL_KEY_FILE')
certfile = os.getenv('SSL_CERT_FILE')

# Server hooks for monitoring and lifecycle management
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_fork(server, worker):
    # Each worker gets its own database connections
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    
    # Could initialize per-worker resources here
    # Example: worker-specific cache connection
    
def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def pre_request(worker, req):
    worker.log.debug("%s %s" % (req.method, req.path))

def post_request(worker, req, environ, resp):
    # Log request details for monitoring
    worker.log.debug("%s %s %s" % (req.method, req.path, resp.status))

def child_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)

# Production optimizations
if os.getenv('ENVIRONMENT') == 'production':
    # Preload application for better memory usage
    preload_app = True
    
    # Disable reload in production
    reload = False
    
    # More aggressive worker recycling
    max_requests = 500
    max_requests_jitter = 100
else:
    # Development settings
    reload = True
    reload_extra_files = [
        '/app/shared/',
    ]