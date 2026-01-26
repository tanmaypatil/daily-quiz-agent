import os
from flask import Flask
from app.config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Allow OAuth over HTTP for local development
    if app.debug or os.environ.get('FLASK_ENV') == 'development':
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.quiz import quiz_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # Create tables
    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
