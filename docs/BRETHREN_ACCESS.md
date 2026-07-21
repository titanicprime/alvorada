# Brethren GitHub Access Runbook

Each brethren execution environment must have authenticated GitHub access.

## Supported Authentication Approaches

1. GitHub MCP server.
2. Dedicated GitHub App.
3. Fine-grained personal access token for a service account.

## Recommended Access Model

- Use one GitHub App or one service account per brethren environment.
- Grant read access to `main`.
- Grant write access only to member branches.
- Allow opening pull requests.
- Disallow direct push to `main`.
- Disallow merge permissions.
- Disallow repository administration permissions.
- Grant no secrets access beyond what is strictly required.

## Minimum GitHub Permissions

Repository permissions:

- Contents: Read and write
- Pull requests: Read and write
- Issues: Read and write
- Metadata: Read-only

Optional:

- Actions: Read-only

## Non-Negotiables

- Making a repository public does not provide write access.
- Credentials must never be committed.
- Tokens must be stored in environment secrets.
- André retains merge authority.

## No-Write-Access Operating Mode

- Public repository access permits anonymous reads but not pushes.
- Lack of GitHub credentials does not block mission participation.
- Brethren may return outputs through their native chat environment.
- André saves each output as a separate UTF-8 text file.
- GitHub Copilot or another authorized operator imports the file.
- Direct GitHub credentials should not be provisioned merely for convenience if the environment cannot store them securely.

This mode preserves:

- Independent cognition.
- Provenance.
- Attribution.
- Lineage.
- Collection discipline.
- Human merge authority.
