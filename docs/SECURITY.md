# Security

## Deployment modes

### Academic demo mode (`AUTH_ENABLED=false`)

- Every visitor is mapped to one shared account.
- There is no isolation between visitors.
- Intended for a laptop, a lab workstation or a trusted internal network.
- **Never expose demo mode to the public internet.**

### Authenticated mode (`AUTH_ENABLED=true`)

- Accounts are required.
- The browser receives an HttpOnly `access_token` cookie after login.
  API clients may instead send `Authorization: Bearer <token>`.
- Passwords are hashed with bcrypt (cost 12).
- Tokens are HS256 JWTs with an explicit expiry
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 720 minutes).
- Set `ALLOW_REGISTRATION=false` after provisioning accounts.

The frontend includes a login/registration page and route guard. Plain
`<img>` and PDF download requests work because authentication uses the
HttpOnly cookie, not a JavaScript-managed token.

## Secrets

Required in production:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | JWT signing key; use at least 32 random bytes |
| `POSTGRES_PASSWORD` | Database password |
| `ML_SERVICE_API_KEY` | Shared token between backend and ML service |

Generate values with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never commit `.env`, bake secrets into images, or send the ML service token
to the browser. Compose prod refuses to start if required secrets are unset.

## Network exposure

Production reference topology:

- Only the frontend container publishes a port.
- PostgreSQL and the ML service are attached to an internal Docker network
  with no host port.
- The backend is reachable only through the frontend's nginx proxy.
- Terminate TLS at a reverse proxy or load balancer in front of the frontend.
- If you publish ports for debugging, bind them to `127.0.0.1`.

The ML service enforces `X-Service-Token` on every endpoint except `/health`
when `ML_SERVICE_API_KEY` is set. Its endpoints must never be exposed
publicly.

## Upload handling

- Size limit before reading the body (`MAX_UPLOAD_BYTES`, default 12 MiB).
- Pixel and dimension limits prevent decompression bombs.
- Format is determined by decoding the content, not by the filename or the
  client-supplied MIME type.
- The original filename is stored as display metadata only and is never used
  to build a filesystem path.
- Storage keys are random; owner IDs are checked on every access.
- SHA-256 is recorded for integrity and duplicate detection.
- HTML/SVG are not accepted image formats, which avoids stored-XSS vectors.

nginx also caps request bodies at 12 MB. Keep `client_max_body_size` and
`MAX_UPLOAD_BYTES` in sync if you change the limit.

## Application hardening

- SQL access goes through SQLAlchemy with bound parameters. No raw SQL is
  built from user input.
- Authorization is enforced by owner checks in repositories and services;
  cross-account access returns `404`, not `403`, to avoid confirming that an
  object exists.
- Internal errors return a generic message; details stay in server logs.
- CORS defaults to the local development origins. Set `ALLOWED_ORIGINS` to
  your exact production origin. Do not use `*` with credentials.
- Security headers are set by nginx (`X-Content-Type-Options`,
  `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`).
- The frontend renders text through React, which escapes by default. Do not
  introduce `dangerouslySetInnerHTML`.

## Known gaps

- No rate limiting, account lockout or CAPTCHA. Put the app behind a reverse
  proxy or identity-aware proxy that provides these controls.
- No email verification or password reset flow.
- No CSRF token. The session cookie is `SameSite=Lax`, and every
  state-changing endpoint uses POST/PATCH/DELETE with JSON or multipart
  content, which cross-site HTML forms cannot forge with the cookie attached.
  If you change cookie semantics, add CSRF protection.
- No virus scanning of uploaded files.
- No liveness or presentation-attack detection.
- The ML service trusts the backend; it does not implement per-user
  authorization.

## Biometric data and ethics

Palmprint images are biometric data and may be personal data under GDPR,
BIPA and similar laws.

- Obtain informed consent and a lawful basis before collecting samples.
- Use authorised datasets only. The repository bundles no biometric data.
- Define retention (`RETENTION_DAYS`, `ML_ARTIFACT_RETENTION_HOURS`) and
  deletion procedures.
- Do not use this platform for identification, surveillance, law enforcement
  or medical diagnosis.
- Similarity scores are uncalibrated. They are not verification decisions and
  must not be presented as probabilities.
- Document algorithm versions and parameters for every reported result.

## Dependency and image hygiene

- Python dependencies are exact-pinned.
- Frontend dependencies are locked in `package-lock.json`; the image uses
  `npm ci`.
- Containers run as a non-root user (`appuser`, UID 10001).
- Base images are minimal (`python:3.12-slim`, `node:20-alpine`,
  `nginx:stable-alpine`).
- Scan images in CI before deployment:

```bash
docker scout cves <image>
# or
trivy image <image>
```

## Reporting a vulnerability

Do not open a public issue for a security problem. Contact the maintainers
privately with reproduction steps and affected versions. Allow time for a fix
before disclosure.
