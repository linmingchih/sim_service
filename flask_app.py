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


@app.route('/')
def index():
    return redirect(url_for('dashboard')) if current_user.is_authenticated else redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
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
    users = User.query.all()
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
        'admin.html', users=users, stats=stats,
        tasks=tasks_query, q=q
    )


@app.route('/admin/archive/<int:task_id>', methods=['POST'])
@login_required
def archive_task(task_id):
    if not current_user.is_admin:
        abort(403)
    task = Task.query.get_or_404(task_id)
    task.archived = True
    db.session.commit()
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)