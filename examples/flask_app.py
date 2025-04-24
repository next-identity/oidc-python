from flask import Flask, render_template_string, url_for, redirect
from next_identity_oidc import NextIdentityFlask

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Change this in production!

# Initialize Next Identity OIDC integration
auth = NextIdentityFlask(
    app=app,
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="http://localhost:5000/auth/callback",
    discovery_url="https://your-next-identity-domain/.well-known/openid-configuration",
)

# Simple HTML template with login/logout buttons
TEMPLATE = """
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
    <h1>Next Identity OIDC Example</h1>
    
    <div>
        {% if is_authenticated %}
            <a href="{{ url_for('logout') }}" class="button">Logout</a>
            <a href="{{ url_for('profile') }}" class="button">Edit Profile</a>
        {% else %}
            <a href="{{ url_for('login') }}" class="button">Login</a>
            <a href="{{ url_for('register') }}" class="button">Register</a>
        {% endif %}
    </div>
    
    {% if user_info %}
    <div class="user-info">
        <h2>User Information</h2>
        <pre>{{ user_info|tojson(indent=2) }}</pre>
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
"""

@app.route("/")
def index():
    """Home page with login/register/profile/logout buttons"""
    return render_template_string(
        TEMPLATE,
        is_authenticated=auth.is_authenticated(),
        user_info=auth.get_user_info(),
        protected_content=False
    )

@app.route("/login")
def login():
    """Handle login"""
    return auth.login(return_to=url_for("index", _external=True))

@app.route("/register")
def register():
    """Handle registration"""
    return auth.register(return_to=url_for("index", _external=True))

@app.route("/profile")
def profile():
    """Handle profile editing"""
    return auth.edit_profile(return_to=url_for("index", _external=True))

@app.route("/logout")
def logout():
    """Handle logout"""
    return auth.logout(return_to=url_for("index", _external=True))

@app.route("/protected")
@auth.login_required
def protected():
    """Protected route that requires authentication"""
    return render_template_string(
        TEMPLATE,
        is_authenticated=True,
        user_info=auth.get_user_info(),
        protected_content=True
    )

if __name__ == "__main__":
    app.run(debug=True) 