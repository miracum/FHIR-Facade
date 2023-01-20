import multiprocessing
import os

bind = "0.0.0.0:" + os.getenv("FACADE_PORT", 8082)
workers = os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1)
accesslog = "-"
preload_app = True
