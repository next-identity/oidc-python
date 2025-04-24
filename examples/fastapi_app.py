from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json
import uvicorn

from next_identity_oidc import NextIdentityFastAPI

app = FastAPI()

# Initialize Next Identity OIDC integration
auth = NextIdentityFastAPI(
    app=app,
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:8000/auth/callback",
    discovery_url="https://your-next-identity-domain/.well-known/openid-configuration",
    secret_key="your-secret-key",  # Change this in production!
)

# Set up templates directory
templates = Jinja2Templates(directory="templates")

# For simplicity, create the template programmatically
Path("templates").mkdir(exist_ok=True)
with open("templates/index.html", "w") as f:
    f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Next Identity OIDC Example</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .button { display: inline-block; padding: 10px 15px; background: #4a90e2; color: white; 
                 text-decoration: none; border-radius: 5px; margin-right: 10px; }
        .user-info { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-top: 20px; }
    </style>
</head>
<body>
    <h1>Next Identity OIDC Example (FastAPI)</h1>
    
    <div>
        {% if is_authenticated %}
            <a href="/logout" class="button">Logout</a>
            <a href="/edit-profile" class="button">Edit Profile</a>
        {% else %}
            <a href="/login" class="button">Login</a>
            <a href="/register" class="button">Register</a>
        {% endif %}
    </div>
    
    {% if user_info %}
    <div class="user-info">
        <h2>User Information</h2>
        <pre>{{ user_info_json }}</pre>
    </div>
    {% endif %}
    
    {% if protected_content %}
    <div class="user-info">
        <h2>Protected Content</h2>
        <p>This content is only visible to authenticated users.</p>
    </div>
    {% endif %}
</body>
</html>
""")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Home page with login/register/profile/logout buttons"""
    user_info = auth.get_user_info(request)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_authenticated": auth.is_authenticated(request),
            "user_info": user_info,
            "user_info_json": json.dumps(user_info, indent=2) if user_info else None,
            "protected_content": False
        }
    )

@app.get("/login")
async def login(request: Request):
    """Handle login"""
    return auth.login(request, return_to="/")

@app.get("/register")
async def register(request: Request):
    """Handle registration"""
    return auth.register(request, return_to="/")

@app.get("/edit-profile")
async def edit_profile(request: Request):
    """Handle profile editing"""
    return auth.edit_profile(request, return_to="/")

@app.get("/logout")
async def logout(request: Request):
    """Handle logout"""
    return auth.logout(request, return_to="/")

@app.get("/protected", response_class=HTMLResponse)
async def protected(request: Request, _=Depends(auth.login_required())):
    """Protected route that requires authentication"""
    user_info = auth.get_user_info(request)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_authenticated": True,
            "user_info": user_info,
            "user_info_json": json.dumps(user_info, indent=2) if user_info else None,
            "protected_content": True
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 