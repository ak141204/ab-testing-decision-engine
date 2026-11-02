# Security Policy

## Supported versions

The project is currently under active development. No formal version-support schedule has been established yet.

## Reporting a vulnerability

Please do not disclose exploitable security vulnerabilities in a public GitHub Issue.

Instead, use GitHub's **Private vulnerability reporting** feature for this repository if it is enabled. If it is not enabled, contact the repository maintainer privately through the contact details available on the maintainer's GitHub profile.

Include, where possible:

- A description of the issue.
- Steps to reproduce it.
- The potential impact.
- A suggested mitigation, if known.

Please allow the maintainer reasonable time to investigate and coordinate a fix before public disclosure.

## Security considerations in the current implementation

The current application is a development/demo project, not a hardened production service.

Known areas requiring review include:

- The API currently allows all CORS origins.
- The API returns raw exception text in HTTP 500 responses.
- The frontend inserts API-provided reasoning strings using `innerHTML`; untrusted content could create a cross-site scripting risk.
- The API request model does not currently define explicit numeric range constraints.
- No authentication or authorization layer is currently implemented.

Do not deploy the current configuration with sensitive data or expose it as a public production service without appropriate security review and hardening.
