# Gunicorn configuration file for Render deployment
import multiprocessing
import os

# Bind to the port provided by Render
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"

# Worker configuration
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'medtoxai-backend'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

# Preload application code before worker processes are forked
preload_app = True

# Restart workers after this many requests
max_requests = 1000
max_requests_jitter = 50

# Environment variables
raw_env = [
    'PYTHONUNBUFFERED=1',
]

def on_starting(server):
    """Called just before the master process is initialized."""
    print("🚀 Starting MedToXAi Backend Server")
    print(f"🌐 Binding to: {bind}")
    print(f"👷 Workers: {workers}")

def on_reload(server):
    """Called when worker is reloaded."""
    print("🔄 Server reloading...")

def when_ready(server):
    """Called just after the server is started."""
    print("✅ Server is ready. Accepting connections")

def on_exit(server):
    """Called just before exiting."""
    print("👋 Server shutting down")
