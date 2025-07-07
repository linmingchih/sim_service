from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, abort
)
from werkzeug.security import generate_password_hash
from flask_login import login_required, current_user
from sqlalchemy import or_

from .models import db, User, Task
from .plugin_loader import scan_plugins, load_registry, save_registry

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin', endpoint='admin')
@login_required
def admin():
    """Redirect /admin to the task statistics page."""
    return redirect(url_for('admin.admin_tasks'))


@admin_bp.route('/admin/tasks', endpoint='admin_tasks')
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


@admin_bp.route('/admin/users', endpoint='admin_users')
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


@admin_bp.route('/admin/archive/<int:task_id>', methods=['POST'], endpoint='archive_task')
@login_required
def archive_task(task_id):
    if not current_user.is_admin:
        abort(403)
    task = Task.query.get_or_404(task_id)
    task.archived = True
    db.session.commit()
    return redirect(url_for('admin.admin_tasks'))


@admin_bp.route('/admin/users/add', methods=['POST'], endpoint='add_user')
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
        return redirect(url_for('admin.admin_users'))
    if User.query.filter_by(username=username).first():
        flash('Username already exists')
        return redirect(url_for('admin.admin_users'))
    user = User(
        username=username,
        password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
        real_name=real_name,
        department=department,
        email=email,
        phone=phone,
        is_admin=is_admin_flag,
    )
    db.session.add(user)
    db.session.commit()
    flash('User added')
    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'], endpoint='edit_user')
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
            user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user.is_admin = bool(request.form.get('is_admin'))
        db.session.commit()
        flash('User updated')
        return redirect(url_for('admin.admin_users'))
    return render_template('edit_user.html', user=user)


@admin_bp.route('/admin/users/delete/<int:user_id>', methods=['POST'], endpoint='delete_user')
@login_required
def delete_user(user_id):
    """Delete a user from the admin panel."""
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    if user.username == 'admin':
        flash('Cannot delete admin user')
        return redirect(url_for('admin.admin_users'))
    db.session.delete(user)
    db.session.commit()
    flash('User deleted')
    return redirect(url_for('admin.admin_users'))


@admin_bp.route('/admin/apps', methods=['GET', 'POST'], endpoint='admin_apps')
@login_required
def admin_apps():
    """Manage plugin enable/disable status."""
    if not current_user.is_admin:
        abort(403)
    registry = load_registry()
    if request.method == 'POST':
        name = request.form.get('name')
        enabled = request.form.get('enabled') == '1'
        registry[name] = enabled
        save_registry(registry)
        return redirect(url_for('admin.admin_apps'))
    plugins = scan_plugins()
    return render_template('admin_apps.html', plugins=plugins)
