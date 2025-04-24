# Next Identity OIDC Python SDK

A simple Python library for integrating with Next Identity via OpenID Connect (OIDC).

This SDK provides easy integration with Next Identity authentication, including the standard OIDC flows and Next Identity-specific features such as registration and profile editing.

## Features

- Standard OIDC authorization code flow for confidential clients
- Automatic discovery of OIDC endpoints
- User authentication and token handling
- Next Identity extensions for registration and profile editing
- Ready-to-use integrations for Flask and FastAPI
- Simple API for accessing user information

## Installation

```bash
pip install next-identity-oidc
```

For Flask integration:

```bash
pip install next-identity-oidc[flask]
```

For FastAPI integration:

```bash
pip install next-identity-oidc[fastapi]
```

Or install all integrations:

```bash
pip install next-identity-oidc[all]
```

## Basic Usage

### Core Client

```python
from next_identity_oidc import NextIdentityClient

# Initialize the client
client = NextIdentityClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:5000/auth/callback",
    discovery_url="https://your-next-identity-domain/.well-known/openid-configuration"
)

# Get login URL
login_url = client.get_login_url()

# Get registration URL
register_url = client.get_register_url()

# Get profile editing URL
profile_url = client.get_profile_url()

# Exchange code for tokens
tokens = client.exchange_code_for_tokens("authorization_code")

# Get user info
user_info = client.get_userinfo(tokens["access_token"])

# Get logout URL
logout_url = client.get_logout_url(id_token_hint=tokens["id_token"])
```

## Flask Integration

```python
from flask import Flask, redirect, url_for
from next_identity_oidc import NextIdentityFlask

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Change this in production!

# Initialize the integration
auth = NextIdentityFlask(
    app=app,
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:5000/auth/callback",
    discovery_url="https://your-next-identity-domain/.well-known/openid-configuration"
)

# Login route
@app.route("/login")
def login():
    return auth.login(return_to=url_for("index", _external=True))

# Registration route
@app.route("/register")
def register():
    return auth.register(return_to=url_for("index", _external=True))

# Profile editing route
@app.route("/profile")
def profile():
    return auth.edit_profile(return_to=url_for("index", _external=True))

# Logout route
@app.route("/logout")
def logout():
    return auth.logout(return_to=url_for("index", _external=True))

# Protected route
@app.route("/protected")
@auth.login_required
def protected():
    # This route is only accessible to authenticated users
    user_info = auth.get_user_info()
    return f"Hello, {user_info.get('name', 'User')}!"

# Home route
@app.route("/")
def index():
    if auth.is_authenticated():
        user_info = auth.get_user_info()
        return f"Logged in as: {user_info.get('name', 'User')}"
    else:
        return "Not logged in"

if __name__ == "__main__":
    app.run(debug=True)
```

## FastAPI Integration

```python
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from next_identity_oidc import NextIdentityFastAPI

app = FastAPI()

# Initialize the integration
auth = NextIdentityFastAPI(
    app=app,
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8000/auth/callback",
    discovery_url="https://your-next-identity-domain/.well-known/openid-configuration",
    secret_key="your-secret-key"  # Change this in production!
)

# Login route
@app.get("/login")
async def login(request: Request):
    return auth.login(request, return_to="/")

# Registration route
@app.get("/register")
async def register(request: Request):
    return auth.register(request, return_to="/")

# Profile editing route
@app.get("/edit-profile")
async def edit_profile(request: Request):
    return auth.edit_profile(request, return_to="/")

# Logout route
@app.get("/logout")
async def logout(request: Request):
    return auth.logout(request, return_to="/")

# Protected route
@app.get("/protected")
async def protected(request: Request, _=Depends(auth.login_required())):
    user_info = auth.get_user_info(request)
    return {"message": f"Hello, {user_info.get('name', 'User')}!"}

# Home route
@app.get("/")
async def index(request: Request):
    if auth.is_authenticated(request):
        user_info = auth.get_user_info(request)
        return {"logged_in": True, "user": user_info}
    else:
        return {"logged_in": False}
```

## Complete Example Applications

Check out the examples directory for complete working applications:

- `examples/flask_app.py`: Flask example with templates and authentication flow
- `examples/fastapi_app.py`: FastAPI example with templates and authentication flow
- `examples/simple_client.py`: Pure Python example using a local HTTP server for callback

## Authentication Flow

This SDK implements the standard OIDC Authorization Code Flow:

1. Redirect the user to the authorization endpoint (login, register, or profile)
2. User authenticates and authorizes your application
3. User is redirected back to your redirect URI with an authorization code
4. Your application exchanges the code for tokens
5. Your application uses the access token to get user information
6. Your application stores the tokens and user info for future use

## Next Identity Specific Features

Next Identity extends the standard OIDC flow with additional features:

### Registration

Registration uses the same flow as login but directs users to a registration form. 
Use `get_register_url()` or the `register()` method to initiate registration.

### Profile Editing

Profile editing allows users to update their account information.
Use `get_profile_url()` or the `edit_profile()` method to initiate profile editing.

## License

MIT
