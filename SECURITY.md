# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email the maintainers directly at [INSERT SECURITY EMAIL]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### Security Best Practices

When using Agentic Swarm:

1. **Never commit credentials**
   - Use environment variables for API keys
   - Add `.env` files to `.gitignore`

2. **Use encryption for sensitive data**
   ```python
   from agentic_swarm.compliance import Encryption
   
   crypto = Encryption(Encryption.generate_key())
   encrypted = crypto.encrypt("sensitive data")
   ```

3. **Enable data isolation in production**
   ```python
   agent = Agent(
       name="secure_agent",
       enable_isolation=True,
       tenant_id="your_tenant",
   )
   ```

4. **Use audit logging**
   ```python
   from agentic_swarm.compliance import AuditLogger
   
   audit = AuditLogger(log_path="./audit.log")
   ```

5. **Set appropriate sandbox limits**
   ```python
   from agentic_swarm.lifecycle import SandboxConfig
   
   config = SandboxConfig(
       memory_limit_mb=256,
       timeout_seconds=30,
       allow_network=False,
   )
   ```

## Security Features

Agentic Swarm includes built-in security features:

- **Audit Logging**: Immutable logs with tamper-proof checksums
- **Encryption**: AES-256 encryption at rest with key rotation
- **Data Isolation**: Namespace-based agent isolation
- **Access Control**: Fine-grained RBAC for permissions, tools, and models
- **Sandbox Execution**: CPU, memory, and timeout limits

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities.
