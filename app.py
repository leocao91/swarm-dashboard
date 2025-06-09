from flask import Flask, render_template, redirect, url_for, request, session
from functools import wraps
import subprocess, shlex
import docker
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

USERNAME = os.environ.get('DASHBOARD_USERNAME', 'admin')
PASSWORD = os.environ.get('DASHBOARD_PASSWORD', '@amin@')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

def get_node_hostname(node_id):
    try:
        node = client.nodes.get(node_id)
        return node.attrs['Description']['Hostname']
    except Exception:
        return None

@app.route('/')
@login_required
def index():
    selected_node = request.args.get('node')
    selected_stack = request.args.get('stack')
    selected_status = request.args.get('status')
    search_query = request.args.get('search', '').strip().lower()

    services = client.services.list()
    stacks = {}

    nodes = [n for n in client.nodes.list() if n.attrs['Spec']['Role'] == 'worker']
    node_names = [n.attrs['Description']['Hostname'] for n in nodes]

    stack_names = set()

    for service in services:
        stack_name = service.attrs['Spec']['Labels'].get('com.docker.stack.namespace', 'default')
        stack_names.add(stack_name)

        if selected_stack and stack_name != selected_stack:
            continue

        service_name = service.name
        service_id = service.id

        if search_query and search_query not in service_name.lower():
            continue

        all_tasks = service.tasks(filters={"desired-state": "running"})

        if selected_node:
            filtered_tasks = [
                t for t in all_tasks
                if get_node_hostname(t['NodeID']) == selected_node
            ]
        else:
            filtered_tasks = all_tasks

        running = sum(1 for t in filtered_tasks if t['Status']['State'] == 'running')
        total = len(filtered_tasks)

        if total == 0:
            continue

        if running == total:
            status_icon = "✅"
            status_class = "status-ok"
        elif running > 0:
            status_icon = "⚠️"
            status_class = "status-warning"
        else:
            status_icon = "❌"
            status_class = "status-fail"

        if selected_status:
            if selected_status == "ok" and status_class != "status-ok":
                continue
            elif selected_status == "warning" and status_class != "status-warning":
                continue
            elif selected_status == "fail" and status_class != "status-fail":
                continue

        stacks.setdefault(stack_name, []).append({
            'name': service_name,
            'id': service_id,
            'image': service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image'],
            'replicas': f"{running}/{total}",
            'status_icon': status_icon,
            'status_class': status_class
        })

    return render_template(
        'index.html',
        stacks=stacks,
        nodes=node_names,
        selected_node=selected_node,
        stack_names=sorted(stack_names),
        selected_stack=selected_stack,
        selected_status=selected_status,
        search_query=search_query
    )

@app.route('/update_service', methods=['POST'])
@login_required
def update_service():
    service_id = request.form.get('service_id')
    if not service_id:
        return redirect(url_for('index'))

    try:
        service = client.services.get(service_id)
        service_name = service.name
        spec = service.attrs['Spec']
        current_force = spec['TaskTemplate'].get('ForceUpdate', 0)
        service.update(force_update=current_force + 1)
        return render_template('message.html', message=f"✅ Service <strong>{service_name}</strong> updated successfully!")
    except Exception as e:
        return render_template('message.html', message=f"❌ Failed to update service: {e}")

def get_running_task_id(service_name):
    try:
        output = subprocess.check_output(
            [
                "docker", "service", "ps", service_name,
                "--filter", "desired-state=running",
                "--format", "{{.ID}}"
            ],
            stderr=subprocess.STDOUT
        )
        task_ids = output.decode("utf-8").strip().splitlines()
        if not task_ids:
            return None
        return task_ids[0]
    except subprocess.CalledProcessError:
        return None

def get_service_logs_filtered_by_task_id(service_name):
    try:
        task_id = get_running_task_id(service_name)
        if not task_id:
            return "❌ No running task ID found."
        cmd = f"docker service logs --tail 300 {shlex.quote(service_name)} | grep {task_id}"
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return output.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return f"❌ Error fetching logs: {e.output.decode('utf-8')}"

@app.route('/logs/<service_id>')
@login_required
def logs(service_id):
    try:
        service = client.services.get(service_id)
        logs = get_service_logs_filtered_by_task_id(service.name)
        return render_template('logs.html', logs=logs)
    except Exception as e:
        return render_template('logs.html', logs=f"❌ Error: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
