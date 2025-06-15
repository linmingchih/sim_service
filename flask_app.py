"""Main Flask application for the task platform."""
import os
import json

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, send_from_directory, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import (
    LoginManager, login_user, login_required,
    logout_user, current_user
)
from sqlalchemy import or_

import yaml

from models import db, User, Task


def load_config():
    """Load task configuration from YAML file."""
    with open('task_config.yaml', 'r') as f:
        return yaml.safe_load(f)


def get_task_description(task_type):
    """Return the module level docstring from a task's script."""
    configs = load_config()
    conf = configs.get(task_type)
    if not conf:
        return ''
    script_rel = conf.get('script_path')
    if not script_rel:
        return ''
    script_path = os.path.join(app.root_path, script_rel)
    try:
        import ast
        with open(script_path, 'r') as f:
            module = ast.parse(f.read())
        return ast.get_docstring(module) or ''
    except FileNotFoundError:
        return ''


app = Flask(__name__)
# Secret key for session management; override in environment for production
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'replace-this-secret')
basedir = os.path.abspath(os.path.dirname(__file__))
# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'app.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


# Custom Jinja filter to map task status to Bootstrap text color classes
@app.template_filter('status_color')
def status_color(status):
    """Return Bootstrap color class for a task status."""
    mapping = {
        'SUCCESS': 'success',
        'FAILURE': 'danger',
        'RUNNING': 'primary',
        'PENDING': 'secondary',
    }
    return mapping.get(status, 'secondary')

# Setup Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


with app.app_context():
    db.create_all()

    # Ensure default admin and example user exist
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin'),
            real_name='Administrator',
            is_admin=True,
        )
        db.session.add(admin_user)
    if not User.query.filter_by(username='lin').first():
        lin_user = User(
            username='lin',
            password_hash=generate_password_hash('620104'),
            real_name='Example User',
        )
        db.session.add(lin_user)
    db.session.commit()


@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('admin_tasks')) if current_user.is_admin else redirect(url_for('dashboard'))
    return redirect(url_for('login'))




@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_tasks')) if current_user.is_admin else redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('admin_tasks')) if user.is_admin else redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/task/<task_type>')
@login_required
def task_detail(task_type):
    if current_user.is_admin:
        return redirect(url_for('admin_tasks'))
    configs = load_config()
    if task_type not in configs:
        abort(404)
    description = get_task_description(task_type)
    return render_template('task.html',
                           task_type=task_type,
                           description=description)


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_tasks'))
    configs = load_config()
    tasks_query = Task.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).order_by(Task.create_time.desc()).all()
    tasks_data = []
    for t in tasks_query:
        files = json.loads(t.result_files) if t.result_files else []
        tasks_data.append({'task': t, 'files': files})
    return render_template('dashboard.html', tasks=tasks_data, configs=configs)


@app.route('/dashboard/jobs')
@login_required
def dashboard_jobs():
    if current_user.is_admin:
        return redirect(url_for('admin_tasks'))
    configs = load_config()
    tasks_query = Task.query.filter_by(
        user_id=current_user.id,
        archived=False
    ).order_by(Task.create_time.desc()).all()
    tasks_data = []
    for t in tasks_query:
        files = json.loads(t.result_files) if t.result_files else []
        tasks_data.append({'task': t, 'files': files})
    return render_template('_jobs_table.html', tasks=tasks_data, configs=configs)


@app.route('/submit/<task_type>', methods=['POST'])
@login_required
def submit_task(task_type):
    if current_user.is_admin:
        return redirect(url_for('admin_tasks'))
    configs = load_config()
    if task_type not in configs:
        abort(404)
    params = {}
    if task_type == 'fractal':
        params['depth'] = request.form.get('depth', type=int)
    elif task_type == 'primes':
        params['n'] = request.form.get('n', type=int)
    else:
        abort(400)
    new_task = Task(
        user_id=current_user.id,
        task_type=task_type,
        parameters=json.dumps(params)
    )
    db.session.add(new_task)
    db.session.commit()
    from tasks import run_task
    run_task.delay(new_task.id)
    return redirect(url_for('dashboard'))


@app.route('/download/<int:task_id>/<path:filename>')
@login_required
def download_file(task_id, filename):
    task = Task.query.get_or_404(task_id)
    if task.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    directory = os.path.join(basedir, 'outputs', str(task_id))
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/admin')
@login_required
def admin():
    """Redirect /admin to the task statistics page."""
    return redirect(url_for('admin_tasks'))


@app.route('/admin/tasks')
@login_required
def admin_tasks():
    """Display task statistics and all submitted tasks."""
    if not current_user.is_admin:
        abort(403)
    q = request.args.get('q', '').strip()
    tasks_query = Task.query
    if q:
        filters = []
        if q.isdigit():
            filters.append(Task.id == int(q))
        filters.append(Task.task_type.ilike(f'%{q}%'))
        tasks_query = tasks_query.join(User).filter(
            or_(User.username.ilike(f'%{q}%'), *filters)
        )
    tasks_query = tasks_query.order_by(Task.create_time.desc()).all()
    stats = {}
    for t in Task.query.all():
        entry = stats.setdefault(t.task_type, {'count': 0, 'success': 0, 'total_time': 0.0})
        entry['count'] += 1
        if t.status == 'SUCCESS':
            entry['success'] += 1
        if t.start_time and t.end_time:
            entry['total_time'] += (t.end_time - t.start_time).total_seconds()
    for stype, data in stats.items():
        count = data['count']
        data['success_rate'] = round((data['success'] / count * 100) if count else 0, 2)
        data['avg_time'] = round((data['total_time'] / count) if count else 0, 2)
    return render_template(
        'admin_tasks.html', stats=stats, tasks=tasks_query, q=q
    )


@app.route('/admin/users')
@login_required
def admin_users():
    """Display the user management page with per-user statistics."""
    if not current_user.is_admin:
        abort(403)
    users = User.query.all()
    user_stats = {}
    for u in users:
        total = len(u.tasks)
        success = sum(1 for t in u.tasks if t.status == 'SUCCESS')
        rate = round((success / total * 100) if total else 0, 2)
        user_stats[u.id] = {'total': total, 'success_rate': rate}
    return render_template('admin_users.html', users=users, user_stats=user_stats)


@app.route('/admin/archive/<int:task_id>', methods=['POST'])
@login_required
def archive_task(task_id):
    if not current_user.is_admin:
        abort(403)
    task = Task.query.get_or_404(task_id)
    task.archived = True
    db.session.commit()
    return redirect(url_for('admin_tasks'))


@app.route('/admin/users/add', methods=['POST'])
@login_required
def add_user():
    """Add a new user from the admin panel."""
    if not current_user.is_admin:
        abort(403)
    username = request.form.get('username')
    password = request.form.get('password')
    real_name = request.form.get('real_name')
    department = request.form.get('department')
    email = request.form.get('email')
    phone = request.form.get('phone')
    is_admin_flag = bool(request.form.get('is_admin'))
    if not username or not password:
        flash('Username and password are required')
        return redirect(url_for('admin_users'))
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('admin_users'))
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        real_name=real_name,
        department=department,
        email=email,
        phone=phone,
        is_admin=is_admin_flag,
    )
    db.session.add(user)
    db.session.commit()
    flash('User added')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit an existing user from the admin panel."""
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.real_name = request.form.get('real_name')
        user.department = request.form.get('department')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        password = request.form.get('password')
        if password:
            user.password_hash = generate_password_hash(password)
        user.is_admin = bool(request.form.get('is_admin'))
        db.session.commit()
        flash('User updated')
        return redirect(url_for('admin_users'))
    return render_template('edit_user.html', user=user)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user from the admin panel."""
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot delete admin user')
        return redirect(url_for('admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted')
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    app.run(debug=True)
