import json
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, send_from_directory, abort, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    login_user, login_required, logout_user, current_user
)

from .models import db, User, Task, AppLayout
from .config_utils import load_config, get_task_description

user_bp = Blueprint('user', __name__)


@user_bp.route('/', endpoint='index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_tasks')) if current_user.is_admin else redirect(url_for('user.dashboard'))
    return redirect(url_for('user.login'))


@user_bp.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.admin_tasks')) if current_user.is_admin else redirect(url_for('user.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin.admin_tasks')) if user.is_admin else redirect(url_for('user.dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')


@user_bp.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))


@user_bp.route('/task/<task_type>', endpoint='task_detail')
@login_required
def task_detail(task_type):
    if current_user.is_admin:
        return redirect(url_for('admin.admin_tasks'))
    configs = load_config()
    if task_type not in configs:
        abort(404)
    conf = configs[task_type]
    description = get_task_description(task_type)
    template_name = f"{task_type}/template.html"
    try:
        return render_template(template_name, task_type=task_type, description=description)
    except Exception:
        return render_template(
            'generic_task.html',
            task_type=task_type,
            description=description,
            params=conf.get('params_def', {}),
            metadata=conf.get('metadata', {})
        )


@user_bp.route('/dashboard', endpoint='dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_tasks'))
    configs = load_config()
    layout_obj = AppLayout.query.filter_by(user_id=current_user.id).first()
    layout_names = [list(configs.keys())]
    if layout_obj:
        try:
            saved = json.loads(layout_obj.layout)
            if saved and isinstance(saved[0], list):
                layout_names = [[n for n in row if n in configs] for row in saved]
            else:
                layout_names = [[n for n in saved if n in configs]]
            for n in configs:
                if not any(n in row for row in layout_names):
                    layout_names[-1].append(n)
        except Exception:
            pass
    else:
        layout_obj = AppLayout(user_id=current_user.id, layout=json.dumps(list(configs.keys())))
        db.session.add(layout_obj)
        db.session.commit()

    ordered_rows = [
        [
            {
                'name': n,
                'display': configs[n]['metadata'].get('name', n.capitalize()),
                'url': url_for('user.task_detail', task_type=n)
            }
            for n in row
        ]
        for row in layout_names
    ]

    tasks_query = Task.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).order_by(Task.create_time.desc()).all()
    tasks_data = []
    for t in tasks_query:
        files = json.loads(t.result_files) if t.result_files else []
        html_file = next((f for f in files if f.lower().endswith('.html')), None)
        if html_file:
            files = [f for f in files if f != html_file]
        tasks_data.append({'task': t, 'files': files, 'html_file': html_file})
    return render_template('dashboard.html', tasks=tasks_data, ordered_rows=ordered_rows)




@user_bp.route('/dashboard/jobs', endpoint='dashboard_jobs')
@login_required
def dashboard_jobs():
    if current_user.is_admin:
        return redirect(url_for('admin.admin_tasks'))
    configs = load_config()
    tasks_query = Task.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).order_by(Task.create_time.desc()).all()
    tasks_data = []
    for t in tasks_query:
        files = json.loads(t.result_files) if t.result_files else []
        html_file = next((f for f in files if f.lower().endswith('.html')), None)
        if html_file:
            files = [f for f in files if f != html_file]
        tasks_data.append({'task': t, 'files': files, 'html_file': html_file})
    return render_template('_jobs_table.html', tasks=tasks_data, configs=configs)


@user_bp.route('/submit/<task_type>', methods=['POST'], endpoint='submit_task')
@login_required
def submit_task(task_type):
    if current_user.is_admin:
        return redirect(url_for('admin.admin_tasks'))
    configs = load_config()
    if task_type not in configs:
        abort(404)
    conf = configs[task_type]
    params = {}
    file_params = [n for n, p in conf.get('params_def', {}).items() if p.get('type') == 'file']
    non_file_params = [n for n in conf.get('params_def', {}) if n not in file_params]

    if file_params:
        new_task = Task(user_id=current_user.id, task_type=task_type, parameters=json.dumps({}))
        db.session.add(new_task)
        db.session.commit()
        base_dir = os.path.dirname(current_app.root_path)
        output_dir = os.path.join(base_dir, 'outputs', str(new_task.id))
        os.makedirs(output_dir, exist_ok=True)
        from werkzeug.utils import secure_filename
        for fp in file_params:
            uploaded = request.files.get(fp)
            if not uploaded or uploaded.filename == '':
                flash('No file uploaded')
                return redirect(url_for('user.task_detail', task_type=task_type))
            filename = secure_filename(uploaded.filename)
            uploaded.save(os.path.join(output_dir, filename))
            params[fp] = filename
    else:
        new_task = Task(user_id=current_user.id, task_type=task_type, parameters=json.dumps({}))
        db.session.add(new_task)
        db.session.commit()

    for pname in non_file_params:
        params[pname] = request.form.get(pname)

    new_task.parameters = json.dumps(params)
    db.session.commit()
    from .tasks import schedule_task
    schedule_task(new_task.id)
    return redirect(url_for('user.dashboard'))


@user_bp.route('/download/<int:task_id>/<path:filename>', endpoint='download_file')
@login_required
def download_file(task_id, filename):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    base_dir = os.path.dirname(current_app.root_path)
    directory = os.path.join(base_dir, 'outputs', str(task_id))
    return send_from_directory(directory, filename, as_attachment=True)


@user_bp.route('/view/<int:task_id>/<path:filename>', endpoint='view_file')
@login_required
def view_file(task_id, filename):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    base_dir = os.path.dirname(current_app.root_path)
    directory = os.path.join(base_dir, 'outputs', str(task_id))
    return send_from_directory(directory, filename, as_attachment=False)


@user_bp.route('/delete/<int:task_id>', methods=['POST'], endpoint='delete_task')
@login_required
def delete_task(task_id):
    """Allow a user to delete their task and its output files."""
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id:
        abort(403)
    base_dir = os.path.dirname(current_app.root_path)
    output_dir = os.path.join(base_dir, 'outputs', str(task_id))
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
    task.archived = True
    task.result_files = json.dumps([])
    db.session.commit()
    flash('Task deleted')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/dashboard/save_layout', methods=['POST'], endpoint='save_layout')
@login_required
def save_layout():
    if current_user.is_admin:
        abort(403)
    data = request.get_json(silent=True) or {}
    layout = data.get('layout')
    if not isinstance(layout, list):
        abort(400)
    # allow nested lists representing rows
    if layout and not isinstance(layout[0], list):
        layout_to_save = layout
    else:
        layout_to_save = [row if isinstance(row, list) else [] for row in layout]

    layout_obj = AppLayout.query.filter_by(user_id=current_user.id).first()
    if not layout_obj:
        layout_obj = AppLayout(user_id=current_user.id, layout=json.dumps(layout_to_save))
        db.session.add(layout_obj)
    else:
        layout_obj.layout = json.dumps(layout_to_save)
    db.session.commit()
    return {'status': 'ok'}
