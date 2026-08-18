# Repository Architecture

## Status

This document proposes a governance-engineering model for evolutionary migration. It does
not adopt Constitution version 2.0, supersede existing governance, assign authority, or
resolve an open constitutional question.

The repository carries governance complexity so the human Constitutional Authority does not
need to hold the entire architecture in working memory. Machine rigor may increase only while
human constitutional comprehension remains intact.

## Governance layers

| Layer | Function | Authority boundary |
|---|---|---|
| Constitution | Establishes institutional purpose, foundational powers, constraints, and amendment rules. | Highest internal governance layer, but only when adopted by valid human Constitutional Authority. |
| Organic Governance Code | Implements constitutional rules as reviewable procedures, grants, controls, and decision paths. | Subordinate to the Constitution; cannot enlarge inherited authority. |
| Role and Office Charter | Defines a role or office independently from any person, model, or implementation. | Holds only authority explicitly granted by a valid higher source. |
| Governance State | Records current incumbency, delegations, missions, disputes, and status. | Descriptive state is not itself a source of authority. |
| Technical Standards | Defines formats, protocols, schemas, validators, and interoperability rules. | Technical conformance cannot create constitutional authority or truth. |
| Institutional Memory | Preserves decisions, dissent, failures, supersession, and historical lineage. | Evidence and precedent have only the weight valid governance gives them. |
| Human Control Plane | Presents current governance in plain language for inspection and intervention. | A view, not an independent authority source; generated views are non-authoritative unless explicitly designated. |

## Evolutionary layout

Existing paths remain preserved. Migration may gradually use `governance/`, `offices/`,
`memory/`, `human-control-plane/`, and `tools/` alongside the existing `constitution/`,
`state/`, `missions/`, `schemas/`, `schema/`, `scripts/`, `tests/`, and `docs/` paths.
Placement does not establish authority.

## Control properties

- Every binding rule needs an explicit, scoped, attributable, provenance-bearing authority
  source.
- Proposals, reviews, inspections, adjudications, authorizations, executions,
  certifications, and historical interpretations remain distinguishable.
- Current state, history, technical conformance, and authority are separate claims.
- Supersession preserves prior artifacts and dissent.
- Unknown or disputed facts remain visible.
- Roles remain portable across implementations; reconstruction does not confer identity,
  incumbency, authority, or hidden memory.
- Consequential reliance and execution require governance before the act. Later logging can
  preserve evidence but cannot govern retrospectively.

