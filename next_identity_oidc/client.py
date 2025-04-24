import json
import requests
from urllib.parse import urlencode
from typing import Dict, Any, Optional, List


class NextIdentityClient:
    """
    Client for Next Identity OIDC integration
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        discovery_url: str,
        scope: str = "openid profile email",
        state_handler: Optional[Any] = None
    ):
        """
        Initialize the Next Identity OIDC client
        
        Args:
            client_id: OIDC client ID
            client_secret: OIDC client secret
            redirect_uri: URI to redirect to after authentication
            discovery_url: OIDC discovery endpoint URL
            scope: Space-separated list of scopes to request
            state_handler: Optional custom state handler object
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.discovery_url = discovery_url
        self.scope = scope
        self.state_handler = state_handler
        self.config = None
        
        # Fetch the configuration from the discovery endpoint
        self._fetch_config()
    
    def _fetch_config(self) -> None:
        """Fetch OIDC configuration from the discovery endpoint"""
        try:
            response = requests.get(self.discovery_url)
            response.raise_for_status()
            self.config = response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch OIDC configuration: {str(e)}")
    
    def get_auth_url(self, state: str = None, nonce: str = None, path: str = "/authorize") -> str:
        """
        Get authorization URL for login
        
        Args:
            state: Optional state parameter for CSRF protection
            nonce: Optional nonce parameter for replay protection
            path: Path to use (default is /authorize, can be /register or /personal-details)
            
        Returns:
            Full authorization URL
        """
        if not self.config:
            raise Exception("OIDC configuration not loaded")
        
        # Get the base URL by removing the /.well-known/openid-configuration part
        base_url = self.config["issuer"]
        
        # Build auth parameters
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
        }
        
        if state:
            params["state"] = state
        if nonce:
            params["nonce"] = nonce
        
        # Construct the full URL with custom path
        auth_endpoint = f"{base_url}{path}"
        return f"{auth_endpoint}?{urlencode(params)}"
    
    def get_login_url(self, state: str = None, nonce: str = None) -> str:
        """Get URL for user login"""
        return self.get_auth_url(state, nonce, "/authorize")
    
    def get_register_url(self, state: str = None, nonce: str = None) -> str:
        """Get URL for user registration"""
        return self.get_auth_url(state, nonce, "/register")
    
    def get_profile_url(self, state: str = None, nonce: str = None) -> str:
        """Get URL for editing user profile"""
        return self.get_auth_url(state, nonce, "/personal-details")
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens
        
        Args:
            code: Authorization code received from the auth server
            
        Returns:
            Dict containing tokens (access_token, id_token, etc.)
        """
        if not self.config:
            raise Exception("OIDC configuration not loaded")
        
        token_endpoint = self.config["token_endpoint"]
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_endpoint, data=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")
    
    def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using the access token
        
        Args:
            access_token: Access token received from token endpoint
            
        Returns:
            Dict containing user information
        """
        if not self.config:
            raise Exception("OIDC configuration not loaded")
        
        userinfo_endpoint = self.config["userinfo_endpoint"]
        
        try:
            response = requests.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get user info: {str(e)}")
    
    def get_logout_url(self, id_token_hint: str = None, post_logout_redirect_uri: str = None) -> str:
        """
        Get URL for user logout
        
        Args:
            id_token_hint: Optional ID token to identify the user session
            post_logout_redirect_uri: Optional URI to redirect to after logout
            
        Returns:
            Full logout URL
        """
        if not self.config:
            raise Exception("OIDC configuration not loaded")
        
        if "end_session_endpoint" not in self.config:
            raise Exception("Logout endpoint not found in OIDC configuration")
            
        params = {}
        if id_token_hint:
            params["id_token_hint"] = id_token_hint
        if post_logout_redirect_uri:
            params["post_logout_redirect_uri"] = post_logout_redirect_uri
        
        logout_endpoint = self.config["end_session_endpoint"]
        
        if params:
            return f"{logout_endpoint}?{urlencode(params)}"
        return logout_endpoint
    
    def validate_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Basic validation and decoding of ID token
        
        Args:
            id_token: ID token to validate
            
        Returns:
            Dict containing decoded ID token payload
        """
        # This is a simplified implementation - in production,
        # use a proper library like python-jose to validate JWT signatures
        
        parts = id_token.split('.')
        if len(parts) != 3:
            raise Exception("Invalid ID token format")
            
        # Decode the payload (middle part)
        import base64
        payload = parts[1]
        # Fix padding
        padding = '=' * (4 - len(payload) % 4)
        payload = payload + padding
        
        # Decode base64
        try:
            decoded = base64.b64decode(payload.translate({ord('-'): ord('+'), ord('_'): ord('/')}))
            return json.loads(decoded)
        except Exception as e:
            raise Exception(f"Failed to decode ID token: {str(e)}") 