from flask import Flask
import docker
import requests
import time
import datetime
import threading
import os

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "http://localhost:5000/api/push-metrics")
PUSH_INTERVAL = int(os.environ.get("PUSH_INTERVAL", 10))
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "secret-token")


def get_metrics():
    metrics = []
    now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    for container in client.containers.list():
        try:
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            num_cpus = len(stats["cpu_stats"]["cpu_usage"].get("percpu_usage", [])) or 1

            cpu_percent = 0.0
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

            mem_usage = stats["memory_stats"]["usage"]
            mem_limit = stats["memory_stats"].get("limit", 1)
            mem_percent = (mem_usage / mem_limit) * 100.0 if mem_limit > 0 else 0.0

            service_name = container.labels.get("com.docker.swarm.service.name", container.name)

            metrics.append({
                "service": service_name,
                "cpu": round(cpu_percent, 2),
                "mem": round(mem_percent, 2),
                "timestamp": now
            })
        except Exception as e:
            print(f"Error: {e}")
    return metrics


def push_loop():
    print("Push loop started...")
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    while True:
        try:
            data = get_metrics()
            if data:
                res = requests.post(DASHBOARD_URL, json=data, headers=headers, timeout=3)
                print("Pushed metrics:", DASHBOARD_URL, "- Status:", res.status_code)
        except Exception as e:
            print("Push failed:", e)
        time.sleep(PUSH_INTERVAL)


@app.route("/health")
def health():
    return "ok", 200

def start_push_thread():
    if not getattr(app, "_push_thread_started", False):
        print("Starting push thread...")
        app._push_thread_started = True
        t = threading.Thread(target=push_loop, daemon=True)
        t.start()

start_push_thread()
