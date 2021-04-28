# oidc_auth_with_google
Simple project for testing and learning SAML2. MS Azure was used as SAML IdP, but could be easily converted to use any.

Application uses Flask, Flask Login-Manager and Jinja2 templates. The actual authN is done by flask_saml2

requirements.txt included.

IdP public key needs to be found at  conf/idp.pem

Following environment variables needs to be set before running: 
```
export ENTITY_ID="XXX"
export SSO_URL="YYY"
export SLO_URL="ZZZ"

```
