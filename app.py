import json
import os
import requests

from flask import Flask, redirect, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

from flask_saml2.utils import certificate_from_file, private_key_from_file
from pathlib import Path
from user import User
from flask import Flask, render_template
from jinja2 import Template
from flask_saml2.sp import ServiceProvider

class DummyServiceProvider(ServiceProvider):
    def get_logout_return_url(self):
        return url_for('index', _external=True)

    def get_default_login_return_url(self):
        return url_for('sso', _external=True)

sp = DummyServiceProvider()
app = Flask(__name__)

KEY_DIR = Path(__file__).parent / 'conf'
print(KEY_DIR)

IDP_CERTIFICATE_FILE = KEY_DIR / 'idp.cer'
IDP_CERTIFICATE = certificate_from_file(IDP_CERTIFICATE_FILE)
ENTITY_ID = os.environ.get("ENTITY_ID", None)
SSO_URL = os.environ.get("SSO_URL", None)
SLO_URL = os.environ.get("SLO_URL", None)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)
app.config['SERVER_NAME'] = 'localhost:9000'
app.config['SAML2_SP'] = {}

app.config['SAML2_IDENTITY_PROVIDERS'] = [
    {
        'CLASS': 'flask_saml2.sp.idphandler.IdPHandler',
        'OPTIONS': {
            'display_name': 'MS Azure IdP',
            'entity_id': ENTITY_ID,
            'sso_url': SSO_URL,
            'slo_url': SLO_URL,
            'certificate': IDP_CERTIFICATE,
        },
    },
]

app.register_blueprint(sp.create_blueprint()) 

login_manager = LoginManager()
login_manager.init_app(app)

# Very volatile userdb
userdb = {}

# This is required for Flask login
@login_manager.user_loader
def load_user(user_id):
    if user_id in userdb:
        return userdb[user_id]
    else:
        return None

@app.route("/", methods=['GET'])
def index():
    return render_template('index.html')

@app.route("/login", methods=['GET'])
def login():
    return redirect(url_for('flask_saml2_sp.login'), code=302)

@app.route("/logout", methods=['GET'])
@login_required
def logout():
    logout_user()
    # Let's not do SLO here
    return redirect(url_for("index"))

@app.route("/sso", methods=['GET'])
def sso():
    # At this point, signature should already be checked by the framework
    auth_data = sp.get_auth_data_in_session()

    print(f"id_: {auth_data.attributes['http://schemas.microsoft.com/identity/claims/objectidentifier']}")
    print(f"given_name: {auth_data.attributes['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname']}")
    print(f"family_name: {auth_data.attributes['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname']}")
    print(f"email: {auth_data.attributes['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress']}")
    print(f"identity_provider: {auth_data.attributes['http://schemas.microsoft.com/identity/claims/identityprovider']}")

    # Create User based on IdP response    
    user = User(
        id_=auth_data.attributes['http://schemas.microsoft.com/identity/claims/objectidentifier'],
        given_name=auth_data.attributes['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname'],
        family_name=auth_data.attributes['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname'],
        email=auth_data.attributes['http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'],

    )

    # Add user to DB indexed by object id
    userdb[auth_data.attributes['http://schemas.microsoft.com/identity/claims/objectidentifier']] = user

    # Flask-Login with user created
    login_user(user)
    
    # We want to use Flask-Login instead of flask-saml2's session
    sp.clear_auth_data_in_session()
 
    # Redirect to front page, now user succesfully logged in
    return redirect(url_for("index"), code=302)

if __name__ == "__main__":
    app.run(ssl_context="adhoc", debug=True)
