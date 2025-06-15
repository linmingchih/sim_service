"""Define Celery tasks for asynchronous task execution."""
import os
import json
import subprocess
from datetime import datetime

from config_utils import load_config

from celery_app import celery
from models import db, Task


@celery.task(bind=True)
def run_task(self, task_id):
    """Celery task to execute a user-submitted script in a virtual environment."""
    task = Task.query.get(task_id)
    if not task:
        return

    # Update task status and start time
    task.status = 'RUNNING'
    task.start_time = datetime.utcnow()
    db.session.commit()

    config = load_config()
    task_conf = config.get(task.task_type, {})
    # expand user and resolve absolute paths for Python executable and script
    from flask import current_app
    venv_python = os.path.expanduser(task_conf.get('venv_python', 'python'))
    script_rel = task_conf.get('script_path')
    script_path = os.path.join(current_app.root_path, script_rel) if script_rel else None

    output_dir = os.path.join('outputs', str(task.id))
    os.makedirs(output_dir, exist_ok=True)

    # Prepare command arguments
    params = json.loads(task.parameters)
    cmd = [venv_python, script_path]
    for key, value in params.items():
        cmd += [f'--{key}', str(value)]

    try:
        # Run the external script
        subprocess.check_call(cmd, cwd=output_dir)
        status = 'SUCCESS'
    except subprocess.CalledProcessError:
        status = 'FAILURE'

    # Generate result.json with list of output files and status
    files = os.listdir(output_dir)
    result = {'files': files, 'status': status}
    with open(os.path.join(output_dir, 'result.json'), 'w') as f:
        json.dump(result, f)

    # Update task record with outcome and completion time
    task.status = status
    task.result_files = json.dumps(files)
    task.end_time = datetime.utcnow()
    db.session.commit()