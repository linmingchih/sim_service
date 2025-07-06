"""Main Flask application for the task platform."""
import os
import sys

# Allow running this file directly from the ``service`` directory.
if __package__ is None or __package__ == "":
    PACKAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    if PACKAGE_PATH not in sys.path:
        sys.path.insert(0, PACKAGE_PATH)
    __package__ = "service"

from flask import Flask
from flask_executor import Executor
from werkzeug.security import generate_password_hash
from flask_login import LoginManager


from .models import db, User, Task
from .user_routes import user_bp
from .admin_routes import admin_bp


# Flask application instance
app = Flask(__name__)
executor = Executor(app)
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
login_manager.login_view = 'user.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()

    # Ensure default admin and example user exist
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            password_hash=generate_password_hash('admin', method='pbkdf2:sha256'),
            real_name='Administrator',
            is_admin=True,
        )
        db.session.add(admin_user)
    if not User.query.filter_by(username='abc').first():
        abc_user = User(
            username='abc',
            password_hash=generate_password_hash('1234', method='pbkdf2:sha256'),
            real_name='Example User',
        )
        db.session.add(abc_user)
    db.session.commit()

app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)


if __name__ == '__main__':
    # Use built-in server in debug mode; otherwise start Waitress for production
    if os.environ.get('FLASK_DEBUG'):  # development convenience
        app.run(debug=True)
    else:
        from waitress import serve

        port = int(os.environ.get('PORT', 5000))
        serve(app, host='0.0.0.0', port=port)
