
# Contributing

Machine-readable artifacts are authoritative in this repository. Documentation explains them but does not override them.

## Workflow

1. Propose changes through patches or pull requests.
2. Update schemas, dictionaries, codebooks, examples, and tests together when the protocol changes.
3. Record canonical dictionary changes in `dictionary/changelog.jsonl`.
4. Increment schema or artifact versions when a normative machine-readable change occurs.
5. Run `make validate` before requesting review.

No agent output becomes canonical automatically.
