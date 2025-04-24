from typing import Dict, Any, Optional, Callable, List
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from .client import NextIdentityClient


class NextIdentityFastAPI:
    """FastAPI integration for Next Identity OIDC"""
    
    def __init__(
        self,
        app: FastAPI = None,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        discovery_url: str = None,
        scope: str = "openid profile email",
        session_auth_key: str = "next_identity_auth",
        callback_path: str = "/auth/callback",
        secret_key: str = None
    ):
        """
        Initialize the FastAPI integration
        
        Args:
            app: FastAPI application instance (optional, can use init_app later)
            client_id: OIDC client ID
            client_secret: OIDC client secret
            redirect_uri: URI to redirect after authentication
            discovery_url: OIDC discovery endpoint URL
            scope: Space-separated list of scopes to request
            session_auth_key: Key to store auth data in session
            callback_path: Path for the auth callback endpoint
            secret_key: Secret key for session encryption
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.discovery_url = discovery_url
        self.scope = scope
        self.session_auth_key = session_auth_key
        self.callback_path = callback_path
        self.secret_key = secret_key
        self.client = None
        
        if app is not None and all([client_id, client_secret, redirect_uri, discovery_url, secret_key]):
            self.init_app(app)
    
    def init_app(self, app: FastAPI, **kwargs):
        """
        Initialize the integration with a FastAPI app
        
        Args:
            app: FastAPI application instance
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
        
        # Add session middleware if secret key is provided
        if self.secret_key:
            app.add_middleware(SessionMiddleware, secret_key=self.secret_key)
        
        # Register callback route
        @app.get(self.callback_path)
        async def auth_callback(request: Request, code: str = None):
            if not code:
                raise HTTPException(status_code=400, detail="Authorization code missing")
                
            try:
                # Exchange code for tokens
                tokens = self.client.exchange_code_for_tokens(code)
                
                # Get user info
                user_info = self.client.get_userinfo(tokens['access_token'])
                
                # Store in session
                request.session[self.session_auth_key] = {
                    'access_token': tokens['access_token'],
                    'id_token': tokens.get('id_token'),
                    'refresh_token': tokens.get('refresh_token'),
                    'expires_in': tokens.get('expires_in'),
                    'user_info': user_info
                }
                
                # Redirect to the return_to URL if available
                return_to = request.session.pop('return_to', '/')
                return RedirectResponse(url=return_to)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Authentication error: {str(e)}")
        
        # Store reference to app
        self.app = app
    
    def login(self, request: Request, return_to: str = '/'):
        """
        Redirect to login page
        
        Args:
            request: FastAPI request object
            return_to: URL to return to after successful login
        """
        request.session['return_to'] = return_to
        login_url = self.client.get_login_url()
        return RedirectResponse(url=login_url)
    
    def register(self, request: Request, return_to: str = '/'):
        """
        Redirect to registration page
        
        Args:
            request: FastAPI request object
            return_to: URL to return to after successful registration
        """
        request.session['return_to'] = return_to
        register_url = self.client.get_register_url()
        return RedirectResponse(url=register_url)
    
    def edit_profile(self, request: Request, return_to: str = '/'):
        """
        Redirect to profile editing page
        
        Args:
            request: FastAPI request object
            return_to: URL to return to after profile editing
        """
        request.session['return_to'] = return_to
        profile_url = self.client.get_profile_url()
        return RedirectResponse(url=profile_url)
    
    def logout(self, request: Request, return_to: str = '/'):
        """
        Logout the user
        
        Args:
            request: FastAPI request object
            return_to: URL to return to after logout
        """
        auth_data = request.session.pop(self.session_auth_key, None)
        
        # If we have an ID token, use it for logout
        id_token = auth_data.get('id_token') if auth_data else None
        
        # Get logout URL with post-logout redirect
        logout_url = self.client.get_logout_url(
            id_token_hint=id_token, 
            post_logout_redirect_uri=return_to
        )
        
        return RedirectResponse(url=logout_url)
    
    def get_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Get user information from session
        
        Args:
            request: FastAPI request object
            
        Returns:
            User information dict or None if not authenticated
        """
        auth_data = request.session.get(self.session_auth_key)
        if auth_data and 'user_info' in auth_data:
            return auth_data['user_info']
        return None
    
    def is_authenticated(self, request: Request) -> bool:
        """
        Check if user is authenticated
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if authenticated, False otherwise
        """
        return (self.session_auth_key in request.session and 
                'access_token' in request.session[self.session_auth_key])
    
    def login_required(self):
        """
        Dependency for protecting routes that require authentication
        
        Returns:
            FastAPI dependency function
        """
        async def dependency(request: Request):
            if not self.is_authenticated(request):
                request.session['return_to'] = str(request.url)
                return RedirectResponse(
                    url="/login", 
                    status_code=status.HTTP_307_TEMPORARY_REDIRECT
                )
            return True
        return Depends(dependency) 