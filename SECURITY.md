# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | Yes       |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please use [GitHub Security Advisories](https://github.com/AgentAnycast/agentanycast/security/advisories/new) to report vulnerabilities privately.

Please include:

1. Description of the vulnerability
2. Steps to reproduce
3. Affected component(s)
4. Impact assessment (if possible)

## Response Timeline

- **Acknowledgement**: within 48 hours
- **Initial assessment**: within 7 days
- **Fix or mitigation**: depends on severity, typically within 30 days

## Security Design

AgentAnycast uses end-to-end encryption (Noise_XX protocol + NaCl box) for all P2P communication. The relay server cannot read message content. See the [Architecture documentation](https://github.com/AgentAnycast/agentanycast/blob/main/docs/architecture.md) for details.

## Disclosure Policy

We follow [coordinated disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure). We will work with you to understand and address the issue before any public disclosure.

## Recognition

We appreciate responsible disclosure and will credit reporters (with permission) in release notes.
