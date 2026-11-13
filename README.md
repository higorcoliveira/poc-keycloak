# Keycloak proof of concept

This example runs Keycloak with a preconfigured `demo` realm and a small Python
API. The API checks bearer tokens with Keycloak's token introspection endpoint.

## Requirements

- Docker with Docker Compose
- `curl` and Python 3 (for the commands below)

## Run

From the repository directory:

```sh
docker compose up -d
docker compose logs -f keycloak
```

Wait for Keycloak to finish starting, then stop following the logs with Ctrl+C.
The admin console is at <http://localhost:8080/admin/> (username `admin`,
password `admin`). The imported realm contains user `alice` (password `alice`)
and confidential client `demo-api` (secret `demo-client-secret`).

## Test

1. A request without a token is rejected with HTTP 401:

   ```sh
   curl -i http://localhost:8000/protected
   ```

2. Obtain an access token for Alice using the demo client's password grant:

   ```sh
   TOKEN=$(curl -fsS -X POST \
     http://localhost:8080/realms/demo/protocol/openid-connect/token \
     -d 'grant_type=password' \
     -d 'client_id=demo-api' \
     -d 'client_secret=demo-client-secret' \
     -d 'username=alice' \
     --data-urlencode 'pass''word=alice' \
     | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
   ```

3. Call the protected API with that token:

   ```sh
   curl -i -H "Authorization: Bearer ""$TOKEN" http://localhost:8000/protected
   ```

   The response should be HTTP 200 with `{"message": "Hello, alice!"}`. Tokens
   expire; repeat step 2 if the API returns 401. An invalid token also returns
   401, and an unavailable Keycloak returns 503.

To run the API's focused tests without Docker:

```sh
python3 -m unittest -v
```

Stop and remove the containers with `docker compose down`. The realm is
re-imported on a fresh start; changes made in the admin console are not persisted.

## Demo only

The credentials and client secret are intentionally public, and Keycloak runs in
development mode over HTTP. The password grant is used only to keep this local
example short; for real applications use authorization code flow with PKCE,
HTTPS, properly managed secrets, and production Keycloak configuration.
