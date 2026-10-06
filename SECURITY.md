# Security

## Reporting a vulnerability

Use [GitHub's private vulnerability reporting form](https://github.com/AliAdilQ/diabetes_risk_prediction/security/advisories/new)
when private reporting is enabled for the repository. If it is unavailable, open an
issue requesting a private reporting channel without including exploit details,
credentials, or sensitive data. The repository owner must enable private reporting
in GitHub settings after uploading the project.

## Deployment checklist

- Use a maintained Python runtime and review dependency advisories before deploying.
- Set `FLASK_ENV=production`, a random `SECRET_KEY` of at least 32 characters, and HTTPS.
- Initialize tables with `flask --app run init-db`; create an administrator using
  `flask --app run create-admin`. Demo seeding refuses to run in production.
- Remove or rotate the local demo account. Never use `Admin@123` publicly.
- Leave debugging disabled. Serve with Waitress behind a properly configured HTTPS proxy.
- The default rate-limit store is process memory and resets on restart. Run one process
  for the local demo. Public deployments need coordinated persistent rate limiting
  at the proxy or a supported shared store and carefully configured trusted proxies.
- Do not enable blanket proxy-header trust; the local app uses the connection IP.
- Restrict admin access and protect database files, backups, CSV exports, and logs.
- Joblib/pickle artifacts can execute code when loaded. Only load this repository's
  trusted artifact or one trained yourself. There is no model upload endpoint.

Passwords use Werkzeug's scrypt hashing. Flask-Login protects every analytics,
record-management, and export route. Flask-WTF checks CSRF on all POST requests,
including JSON requests. Logout and deletion are POST-only. Sessions are HttpOnly,
SameSite=Lax, expire after 30 minutes of inactivity, and use Secure cookies in
production. CSP restricts scripts and other assets to the app's origin.

The application stores entered numeric measurements, timestamps, source, and model
provenance. It does not request names or contact details for predictions. Treat real
health measurements as sensitive: the demo is not designed for clinical use,
regulatory compliance, or collecting patient information. Use fictional inputs.
Admins can delete individual records. The result route uses the submitting browser's
session and does not expose predictable public record URLs. Sensitive pages and API
responses use `Cache-Control: no-store`.
