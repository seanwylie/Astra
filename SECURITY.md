# Security

## Reporting a vulnerability

Please report privately, so a fix can exist before details are public.

Use GitHub's private vulnerability reporting:
**[open a draft advisory](https://github.com/seanwylie/astra/security/advisories/new)**. That
route is preferred over email; there is no published address for this project.

The draft-advisory form only works when
[private vulnerability reporting](https://docs.github.com/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository)
is enabled on the repository. If the form is missing, do not open a public issue.

Please do not open a public issue for a vulnerability, and please do not post exploit material
in public threads.

**Expect a slow response.** This project is maintained as time permits and carries no
production-support commitment. There is no service-level agreement on triage or fixes.

## What is in scope

- Handling of Discord bot tokens, OpenAI keys, and AWS credentials
- Accidental persistence of secrets into mind files, logs, or snapshots
- A path that writes operator conversation content to a public remote by default
- A default configuration that talks to a third-party account the operator did not set

## What is out of scope

- Running Astra with a live Discord token, API key, or public S3 bucket that you chose
- Model output that is merely surprising or unkind
- Issues that require a secret you injected into `.env`

## Secrets

Never commit `.env`, mind files from a live instance, logs, or database files. The repository
ships a synthetic fixture under `fixtures/` so the suite and a first run do not need yours.
