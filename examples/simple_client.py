import json
import webbrowser
import http.server
import socketserver
import urllib.parse
import threading
import time
from typing import Dict, Any, Optional

from next_identity_oidc import NextIdentityClient

# Configuration
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
REDIRECT_URI = "http://localhost:8080/callback"
DISCOVERY_URL = "https://your-next-identity-domain/.well-known/openid-configuration"

# Initialize the client
client = NextIdentityClient(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    discovery_url=DISCOVERY_URL
)

# Global variable to store the authorization code
auth_code = None
code_received_event = threading.Event()

class CallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for authorization callback"""
    
    def do_GET(self):
        """Handle GET request (callback from auth server)"""
        global auth_code
        
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            # Extract the authorization code
            auth_code = params['code'][0]
            
            # Serve success page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            response = f"""
            <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; text-align: center; }}
                    .success {{ color: green; }}
                </style>
            </head>
            <body>
                <h1 class="success">Authentication Successful!</h1>
                <p>You can now close this window and return to the application.</p>
            </body>
            </html>
            """
            
            self.wfile.write(response.encode())
            
            # Signal that we received the code
            code_received_event.set()
        else:
            # Send error response if no code is present
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            self.wfile.write(b"<html><body><h1>Error</h1><p>No authorization code received.</p></body></html>")
    
    def log_message(self, format, *args):
        """Suppress logging"""
        return

def start_callback_server():
    """Start a temporary HTTP server to handle the callback"""
    with socketserver.TCPServer(("", 8080), CallbackHandler) as httpd:
        print("Callback server started at http://localhost:8080")
        
        # Wait for the authorization code or timeout after 5 minutes
        if not code_received_event.wait(300):
            print("Timeout waiting for authorization code")
            return None
        
        print("Authorization code received, shutting down server...")
        
        # Give the browser time to render the success page
        time.sleep(1)
        
        # Shutdown the server
        httpd.server_close()
        
        return auth_code

def authenticate(action: str = "login"):
    """Perform authentication flow"""
    global auth_code
    auth_code = None
    code_received_event.clear()
    
    # Start the callback server in a separate thread
    server_thread = threading.Thread(target=start_callback_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Get the authorization URL based on the action
    if action == "login":
        auth_url = client.get_login_url()
    elif action == "register":
        auth_url = client.get_register_url()
    elif action == "profile":
        auth_url = client.get_profile_url()
    else:
        raise ValueError(f"Invalid action: {action}")
    
    # Open the browser for authentication
    print(f"Opening browser for {action}...")
    webbrowser.open(auth_url)
    
    # Wait for the server thread to complete
    server_thread.join()
    
    if not auth_code:
        print("Authentication failed: No authorization code received")
        return None
    
    # Exchange the code for tokens
    print("Exchanging authorization code for tokens...")
    try:
        tokens = client.exchange_code_for_tokens(auth_code)
        
        # Get user info
        if 'access_token' in tokens:
            print("Getting user info...")
            user_info = client.get_userinfo(tokens['access_token'])
            return {
                'tokens': tokens,
                'user_info': user_info
            }
        else:
            print("No access token received")
            return None
    except Exception as e:
        print(f"Error during token exchange: {str(e)}")
        return None

def print_user_info(user_info: Dict[str, Any]):
    """Print user information in a formatted way"""
    if not user_info:
        print("No user information available")
        return
    
    print("\n=== User Information ===")
    print(f"Subject: {user_info.get('sub', 'N/A')}")
    print(f"Name: {user_info.get('name', 'N/A')}")
    print(f"Email: {user_info.get('email', 'N/A')}")
    
    # Print all other attributes
    print("\nAll Attributes:")
    print(json.dumps(user_info, indent=2))

def main():
    """Main function"""
    while True:
        print("\n=== Next Identity OIDC Client ===")
        print("1. Login")
        print("2. Register")
        print("3. Edit Profile")
        print("4. Exit")
        
        choice = input("Enter your choice (1-4): ")
        
        if choice == "1":
            result = authenticate("login")
            if result:
                print_user_info(result['user_info'])
        elif choice == "2":
            result = authenticate("register")
            if result:
                print_user_info(result['user_info'])
        elif choice == "3":
            result = authenticate("profile")
            if result:
                print_user_info(result['user_info'])
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    main() 