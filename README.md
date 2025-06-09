# Swarm Dashboard

This is a small project using Python to manage Docker Swarm services through a web UI.

Authentication with SSO - Keycloak by OIDC protocol (include Single Logout - SLO)

The dashboard displays the services of each stack on each worker node, the status and replicas of each service, allows updating services, and shows service logs.

## How to:

Git clone repository and run on management node of Docker Swarm cluster
```
mkdir flask_session_dir && chmod 777 flask_session_dir
```

### Build image:
```
docker build -t swarm-dashboard .
```
### Run image:
```
docker run -it -d -p 5000:5000 \
  -e FLASK_SECRET_KEY="supersecretkey" \
  -e KEYCLOAK_BASE_URL="https://localhost:8080/" \  # URL Keycloak
  -e KEYCLOAK_REALM="myrealm" \ # Realm name
  -e KEYCLOAK_CLIENT_ID="client-id" \ # Client ID
  -e KEYCLOAK_CLIENT_SECRET="client-secret" \ #Client secret
  -e REDIRECT_URI="http://localhost:5000/oidc_callback" \ # URL callback service
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd)/flask_session_dir:/app/flask_session_dir \
  --name swarm-dashboard \
  swarm-dashboard
```
### Configuaration SSO - Keycloak:
```
ClientID: myrealm
Valid redirect URIs:  http://localhost:5000/oidc_callback
                      http://localhost:5000/*
Valid post logout redirect URIs: http://localhost:5000/
Web origins: *
