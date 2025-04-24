from functools import wraps
from flask import request, redirect, session, url_for
from typing import Callable, Any, Dict, Optional

from .client import NextIdentityClient


class NextIdentityFlask:
    """Flask integration for Next Identity OIDC"""
    
    def __init__(
        self,
        app=None,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        discovery_url: str = None,
        scope: str = "openid profile email",
        session_auth_key: str = "next_identity_auth",
    ):
        """
        Initialize the Flask integration
        
        Args:
            app: Flask application instance (optional, can use init_app later)
            client_id: OIDC client ID
            client_secret: OIDC client secret
            redirect_uri: URI to redirect after authentication
            discovery_url: OIDC discovery endpoint URL
            scope: Space-separated list of scopes to request
            session_auth_key: Key to store auth data in session
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.discovery_url = discovery_url
        self.scope = scope
        self.session_auth_key = session_auth_key
        self.client = None
        
        if app is not None and all([client_id, client_secret, redirect_uri, discovery_url]):
            self.init_app(app)
    
    def init_app(self, app, **kwargs):
        """
        Initialize the integration with a Flask app
        
        Args:
            app: Flask application instance
            **kwargs: Additional configuration options
        """
        # Update config with values from kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        # Initialize the OIDC client
        self.client = NextIdentityClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            discovery_url=self.discovery_url,
            scope=self.scope
        )
        
        # Register a callback route
        @app.route('/auth/callback')
        def auth_callback():
            # Exchange code for tokens
            code = request.args.get('code')
            if not code:
                return "Authorization code missing", 400
                
            try:
                # Exchange code for tokens
                tokens = self.client.exchange_code_for_tokens(code)
                
                # Get user info
                user_info = self.client.get_userinfo(tokens['access_token'])
                
                # Store in session
                session[self.session_auth_key] = {
                    'access_token': tokens['access_token'],
                    'id_token': tokens.get('id_token'),
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in'),
                    'user_info': user_info
                }
                
                # Redirect to the return_to URL if available
                return_to = session.pop('return_to', '/')
                return redirect(return_to)
            except Exception as e:
                return f"Authentication error: {str(e)}", 400
        
        # Store reference to app
        self.app = app
    
    def login(self, return_to: str = '/'):
        """
        Redirect to login page
        
        Args:
            return_to: URL to return to after successful login
        """
        session['return_to'] = return_to
        login_url = self.client.get_login_url()
        return redirect(login_url)
    
    def register(self, return_to: str = '/'):
        """
        Redirect to registration page
        
        Args:
            return_to: URL to return to after successful registration
        """
        session['return_to'] = return_to
        register_url = self.client.get_register_url()
        return redirect(register_url)
    
    def edit_profile(self, return_to: str = '/'):
        """
        Redirect to profile editing page
        
        Args:
            return_to: URL to return to after profile editing
        """
        session['return_to'] = return_to
        profile_url = self.client.get_profile_url()
        return redirect(profile_url)
    
    def logout(self, return_to: str = '/'):
        """
        Logout the user
        
        Args:
            return_to: URL to return to after logout
        """
        auth_data = session.pop(self.session_auth_key, None)
        
        # If we have an ID token, use it for logout
        id_token = auth_data.get('id_token') if auth_data else None
        
        # Construct absolute URL for post-logout redirect
        post_logout_redirect_uri = url_for('index', _external=True) if return_to == '/' else return_to
        
        # Get logout URL
        logout_url = self.client.get_logout_url(
            id_token_hint=id_token, 
            post_logout_redirect_uri=post_logout_redirect_uri
        )
        
        return redirect(logout_url)
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get user information from session
        
        Returns:
            User information dict or None if not authenticated
        """
        auth_data = session.get(self.session_auth_key)
        if auth_data and 'user_info' in auth_data:
            return auth_data['user_info']
        return None
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.session_auth_key in session and 'access_token' in session[self.session_auth_key]
    
    def login_required(self, f: Callable) -> Callable:
        """
        Decorator to require authentication for a route
        
        Args:
            f: Route function to decorate
            
        Returns:
            Decorated function
        """
        @wraps(f)
        def decorated(*args, **kwargs):
            if not self.is_authenticated():
                session['return_to'] = request.url
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated 