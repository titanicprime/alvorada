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
