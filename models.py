"""Define database models for users and tasks."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

# Initialize the database instance
db = SQLAlchemy()


class User(db.Model, UserMixin):
    """User account model."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    real_name = db.Column(db.String(120))
    department = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    tasks = db.relationship('Task', backref='user', lazy=True)


class Task(db.Model):
    """Task record model."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)
    parameters = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='PENDING', nullable=False)
    result_files = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    archived = db.Column(db.Boolean, default=False, nullable=False)