"""
Google OAuth Authentication
Similar pattern to gmail-chat, supports multiple configured users
"""
import os
import json
import secrets
from flask import Blueprint, redirect, url_for, request, session, flash, current_app
from flask_login import login_user, logout_user, current_user
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)

# OAuth scopes - only need email for identification
SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

# Pending OAuth states (to prevent CSRF)
_pending_states = {}


def _get_client_config():
    """Build OAuth client config from environment variables"""
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    client_secret = current_app.config['GOOGLE_CLIENT_SECRET']

    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set")

    return {
        'web': {
            'client_id': client_id,
            'client_secret': client_secret,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
        }
    }


def _get_redirect_uri():
    """Get OAuth redirect URI"""
    base_url = current_app.config['BASE_URL']
    return f"{base_url}/auth/callback"


@auth_bp.route('/login')
def login():
    """Initiate Google OAuth flow"""
    if current_user.is_authenticated:
        return redirect(url_for('quiz.index'))

    try:
        redirect_uri = _get_redirect_uri()
        client_config = _get_client_config()

        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Store state for CSRF protection
        _pending_states[state] = True
        session['oauth_state'] = state

        return redirect(authorization_url)

    except Exception as e:
        current_app.logger.error(f"Error initiating OAuth: {e}")
        flash('Failed to initiate login. Please try again.', 'error')
        return redirect(url_for('quiz.index'))


@auth_bp.route('/auth/callback')
def callback():
    """Handle OAuth callback from Google"""
    try:
        # Verify state
        state = request.args.get('state')
        if not state or state not in _pending_states:
            flash('Invalid authentication state. Please try again.', 'error')
            return redirect(url_for('quiz.index'))

        del _pending_states[state]

        # Check for errors
        error = request.args.get('error')
        if error:
            flash(f'Authentication failed: {error}', 'error')
            return redirect(url_for('quiz.index'))

        # Complete OAuth flow
        redirect_uri = _get_redirect_uri()
        client_config = _get_client_config()

        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )

        # Handle HTTP vs HTTPS mismatch for local development
        authorization_response = request.url
        if authorization_response.startswith('https://localhost'):
            authorization_response = authorization_response.replace('https://', 'http://', 1)

        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials

        # Get user info from Google
        user_info = _get_user_info(credentials)
        if not user_info:
            flash('Could not retrieve user information.', 'error')
            return redirect(url_for('quiz.index'))

        email = user_info.get('email')
        google_id = user_info.get('id')
        name = user_info.get('name', email.split('@')[0])

        # Check if user is authorized
        authorized_emails = current_app.config.get('AUTHORIZED_EMAILS', [])
        if authorized_emails and email not in authorized_emails:
            flash('You are not authorized to access this application. Contact the administrator.', 'error')
            return redirect(url_for('quiz.index'))

        # Get or create user
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User(
                google_id=google_id,
                email=email,
                name=name
            )
            db.session.add(user)

        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Log in user
        login_user(user, remember=True)

        return redirect(url_for('quiz.index'))

    except Exception as e:
        current_app.logger.error(f"OAuth callback error: {e}")
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('quiz.index'))


def _get_user_info(credentials):
    """Get user info from Google"""
    try:
        service = build('oauth2', 'v2', credentials=credentials)
        return service.userinfo().get().execute()
    except Exception as e:
        current_app.logger.error(f"Error getting user info: {e}")
        return None


@auth_bp.route('/logout')
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('quiz.index'))
