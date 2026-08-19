# Constitutional Compiler Semantic Audit

## Status

This is a non-authoritative engineering audit. It records validator behavior and does not
adopt constitutional law, resolve open constitutional questions, or establish authority.

Passing validation does not establish constitutional correctness, factual truth, or human
authorization. The validator may reject an invalid representation; it cannot create the
authority needed to make that representation valid.

## Corrections

| Defect | Risk | Correction | Test coverage | Residual limitation |
|---|---|---|---|---|
| Consequential Governance Events could omit authority. | A record could represent authorization or execution without a valid grant. | Adjudication, authorization, execution, and certification now require an existing, active, unexpired, actor-entitling, scoped authority source and provenance. | Valid bounded events and missing, inactive, expired, wrong-actor, and excess-scope cases. | Event classification and substantive authority remain human governance questions. |
| Mission grants were checked only for scope. | An inactive or expired grant could appear to create a mission. | Mission sources must exist, be active, be unexpired at state time, and include mission-creation scope. | Active, inactive, expired, nonexistent, and insufficient-scope grants. | The validator does not establish that a recorded grant is constitutionally valid. |
| Foundational authority used derived-authority provenance fields. | Circular or fictional upstream authority could be manufactured, while an unsupported claim could be labeled documented. | Foundational human authority claims and derived grants now use distinct authority bases. Documented foundational provenance requires supporting evidence or an artifact reference; unknown provenance may remain empty, while incomplete and disputed provenance remain representable without an invented source. Derived grants require an upstream source and prohibit self-attestation. | Documented provenance with and without evidence; unknown, incomplete, and disputed provenance; valid derivation, fictional source, and self-attestation cases. | The repository's named human authority remains a recorded claim whose external provenance may be unknown. |
| Lineage checks covered only generic rules and treated all dependencies as governance-object references. | Authorities, delegations, offices, or events could cite missing predecessors, while external artifacts, technical standards, datasets, or processes could be falsely rejected as missing governance objects. | Supersession, replacement, and explicitly declared `governance_dependencies` are checked across supported governance objects. Generic, artifact, and external dependencies remain representable without governance identifier resolution. | Broken and resolved governance references in each supported object collection, plus accepted generic, artifact, and external dependencies. | Historical artifacts are not required to be migrated; only lineage claims and explicitly governance-scoped dependencies made in validated records are checked. |
| Event aggregation retained one actor per function. | A later participant could hide an actor's cross-function participation. | Aggregation now retains actor sets and reports only actor intersections. | Multiple proposal actors with one overlapping authorizer and distinct non-overlapping actors. | The current separation pairs remain structural warnings, not constitutional adjudications. |
| Emergency delegation structure was under-specified. | Emergency authority could lack a trigger, expiry, review, restoration condition, or extension boundary. | Emergency records require active upstream authority, explicit scope and trigger, non-null expiry, review path, termination condition, and prohibited or separately authorized extension. Core bounds cannot be self-redefined. | Valid bounded delegation, missing expiry, excess scope, inactive source, unauthorized extension, and attempted self-redefinition. | No substantive emergency powers, triggers, or duration thresholds are created. |
| Acronym metadata substituted for readable text. | Human-facing text could remain opaque despite metadata. | Every three-letter acronym must be spelled out at every occurrence in explicitly designated human-facing text. Metadata does not satisfy the check. | Missing expansion, metadata-only, rendered expansion, and repeated unexpanded occurrence. | The syntactic check cannot determine whether prose is substantively understandable. |
| Institutional references lacked resolution state. | Missing, external, and unknown references were indistinguishable. | State references now carry resolved, unresolved, external, or unknown status; locally resolved claims are checked against supplied objects. | Valid mixed resolution states and falsely resolved references. | External references are classified, not fetched or factually verified. |
| Equality was presented as effective-power analysis. | A string comparison could imply unsupported institutional analysis. | The comparison is explicitly reported as an experimental placeholder and no longer claims material divergence. | Placeholder reporting without a false divergence warning. | Routing centrality, dependence, reliance frequency, conversion, information access, option suppression, and removal impact remain future design targets. |

## Existing test changes

The authority fixture now represents a foundational human authority claim rather than a
fictional external grant. Consequential event fixtures now provide authority when testing a
valid case. The acronym test no longer treats metadata as expansion, and the effective-power
test expects placeholder status rather than a substantive divergence claim. These changes
remove tests of semantics identified as defective while preserving positive bounded cases.

## Severity discipline

Errors are limited to representations that cannot safely support the governed state they
claim. Warnings preserve representable claims needing human review, including unknown or
incomplete foundational provenance and separation-of-functions intersections. Informational
findings identify non-blocking migration or experimental limitations.

## Unresolved and human authority

This audit does not determine who validly holds foundational authority, which powers are
non-delegable, which event classes should require further independent functions, or what
emergency powers exist. Adoption, refounding, and resolution of those questions require valid
human Constitutional Authority.
