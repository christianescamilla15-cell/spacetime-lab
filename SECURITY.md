# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability in Spacetime Lab, please **do not** open a public issue. Instead, email:

**christianescamilla15@gmail.com**

We'll respond within 72 hours and work with you on a fix.

## Secret Management

This project follows strict secret handling:

### ❌ Never commit
- `.env` files with real values
- API keys (Anthropic, Groq, etc.)
- Database credentials
- Service account JSON files

### ✅ Safe to commit
- `.env.example` with placeholder values
- Public configuration (metric parameters, demo data)

### Pre-commit hook (recommended)

```bash
# Install gitleaks
brew install gitleaks   # macOS
scoop install gitleaks  # Windows

# Enable pre-commit
gitleaks install
```
