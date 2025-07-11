"""Background task execution utilities using :mod:`flask_executor`."""
import os
import json
import subprocess
import html
import fnmatch
from datetime import datetime

from .config_utils import load_config

from .flask_app import app, executor
from flask import has_request_context
from .models import db, Task


def run_task(task_id):
    """Execute a user-submitted script in a virtual environment."""
    # Use application context when running in a background thread
    with app.app_context():
        task = db.session.get(Task, task_id)
        if not task:
            return

        # Update task status and start time
        task.status = 'RUNNING'
        # Use server local time for consistency with displayed timestamps
        task.start_time = datetime.now()
        db.session.commit()

        config = load_config()
        task_conf = config.get(task.task_type, {})
        # expand user and resolve absolute paths for Python executable and script
        from flask import current_app
        venv_python = os.path.expanduser(task_conf.get('venv_python', 'python'))
        if venv_python == 'python':
            import sys
            venv_python = sys.executable
        script_rel = task_conf.get('script_path')
        script_path = os.path.join(current_app.root_path, script_rel) if script_rel else None

        # Determine absolute path for the task's output directory.  The project
        # root is one level above the ``service`` package, so join that with
        # ``outputs/<task_id>`` to ensure paths are consistent regardless of the
        # current working directory.
        base_dir = os.path.dirname(current_app.root_path)
        output_dir = os.path.join(base_dir, 'outputs', str(task.id))
        os.makedirs(output_dir, exist_ok=True)

        # Prepare command arguments
        params = json.loads(task.parameters)
        cmd = [venv_python, script_path]
        for key, value in params.items():
            cmd += [f'--{key}', str(value)]

        try:
            # Run the external script and capture output for error reporting
            result = subprocess.run(
                cmd, cwd=output_dir, capture_output=True, text=True
            )
            status = 'SUCCESS' if result.returncode == 0 else 'FAILURE'
            if status == 'FAILURE':
                error_file = os.path.join(output_dir, 'error.html')
                with open(error_file, 'w') as f:
                    f.write('<html><body><pre>')
                    f.write(html.escape((result.stdout or '') + (result.stderr or '')))
                    f.write('</pre></body></html>')
        except Exception as exc:
            # Unexpected exceptions are also reported as FAILURE
            status = 'FAILURE'
            error_file = os.path.join(output_dir, 'error.html')
            with open(error_file, 'w') as f:
                f.write('<html><body><pre>')
                f.write(html.escape(str(exc)))
                f.write('</pre></body></html>')

        # Generate result.json with list of output files and status
        files = os.listdir(output_dir)
        keep_patterns = task_conf.get("result_keep")
        if keep_patterns:
            kept = set()
            for pat in keep_patterns:
                kept.update(fnmatch.filter(files, pat))
            files = sorted(kept)
        result = {'files': files, 'status': status}
        with open(os.path.join(output_dir, 'result.json'), 'w') as f:
            json.dump(result, f)

        # Update task record with outcome and completion time
        task.status = status
        task.result_files = json.dumps(files)
        # Record completion time in server local timezone
        task.end_time = datetime.now()
        db.session.commit()


def schedule_task(task_id):
    """Submit ``run_task`` to the :class:`~flask_executor.Executor`."""
    if has_request_context():
        return executor.submit(run_task, task_id)
    # When called outside a request context (e.g., stress tests), using
    # ``Executor.submit`` fails because it wraps the function with
    # ``copy_current_request_context``. Submit directly to the underlying
    # executor instead.
    return executor._self.submit(run_task, task_id)
