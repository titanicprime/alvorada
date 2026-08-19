# Governed Response-Envelope Conformance

## Status and scope

This is a technical standard for response serialization. It does not modify Constitution
version 2.0, create a governance event, alter canonical authority, or rewrite historical
responses. The identity registry is a descriptive projection of current repository state and
role files; it does not create standing. The conformance-examination profile is operational
and is not constitutional law or Organic Governance Code.

The change is motivated by serialization and identity failures observed in examination
identifier `ALV-CONFORM-001`.

## Why response envelopes exist

Governance-sensitive inter-agent responses need stable machine coordinates for identity,
provenance, declared authority basis, permitted output class, state effect, and content.
The envelope supplies those coordinates while leaving role-specific analysis inside
`content`.

## What the envelope guarantees

A conformant envelope:

- uses the defined fields and enum values;
- supplies required identity and lifecycle fields;
- matches `member_designation` and `canonical_role` against the resolved identity registry;
- keeps extensions inside the `extensions` object under an `x_` namespace;
- records bounded correction lineage; and
- remains separable from its role-specific content.

Whitespace and typography do not alter semantic validity. Interpretable Markdown decoration
can produce a warning without becoming a constitutional failure.

## What the envelope does not guarantee

Envelope validity does not establish:

- truth;
- authority beyond the referenced grant;
- correctness;
- certification; or
- constitutional legitimacy.

Conformance does not authorize reliance, execution, canonization, or a state transition.
A conformant response still requires human or role review of its substance.

## Identity semantics

Identity is exact and case-sensitive. The validator returns `MATCH`, `MISMATCH`,
`UNKNOWN_MEMBER`, `UNKNOWN_ROLE`, or `UNRESOLVED_REGISTRY`. It never infers or corrects an
identity. A readable response with invalid identity is preserved but remains nonconformant
until corrected.

The registry at `state/response-identities.json` derives its entries from
`state/current.yaml` and the current role files. Historical identity artifacts remain
historical and are not silently normalized.

### Current identity versus historical identity

The registry is a projection of institutional state, not an authority source. A current
identity must be supported by `state/current.yaml` and a current role record. Historical and
superseded identities remain recorded with their own status and lineage; an alias or possible
successor never silently acquires the predecessor's standing. Governed responses therefore
require exact self-identification.

Repository evidence currently supports `Red-1`, `Mr. Gold`, `Blue-0`, and `Sienna-4` as active
registry entries. It does not contain current, historical, or experimental role records for
`Blue-0-Alt`, `Sienna-5`, `Purple Rain`, or `Thucydides`. Those reported designations are
recorded only as `UNCLEAR` gaps, not as members. The possible relationships between
`Blue-0-Alt` and `Blue-0`, and between `Sienna-5` and `Sienna-4`, are also `UNCLEAR`.
Establishing succession, variants, standing, or new roles requires institutional evidence and,
where standing changes, human Constitutional Authority.

An exact historical or superseded designation remains representable but does not return
`MATCH` as a current identity. It is rendered with its status and remains nonconformant where
current identity is required.

## Permitted output classes

`permitted_output_class` supports:

- `RECEIPT`;
- `INFORMATIONAL_OBSERVATION`;
- `ANALYSIS`;
- `PROPOSAL`;
- `REVIEW`;
- `FORMAL_REVIEW`;
- `INSPECTION`;
- `ADJUDICATION`;
- `EXECUTION`;
- `CERTIFICATION`;
- `HISTORICAL_INTERPRETATION`;
- `CHRONOLOGICAL_RECORD`;
- `CONFORMANCE_RESPONSE`; and
- `RECOMMENDATION`.

`RECOMMENDATION` is explicit because the current role records permit recommendations while
withholding authorization. `REVIEW` and `FORMAL_REVIEW` remain separate because governed
communications use both labels; the repository does not yet contain a complete authority rule
that defines their boundary, so that distinction remains operationally ambiguous rather than
silently collapsed.

Message type and permitted output class are independent dimensions. For example, an
`EXAMINATION` message can carry a `CONFORMANCE_RESPONSE` output class. Neither field establishes
substantive authority.

## Correction semantics

A correction names the response it `supersedes`, its registered identity, a defined
`correction`, whether substantive content changed, and its own `state_effect`. When
`substantive_content_changed` is `NO`, unchanged analytical content need not be repeated.
Providing different content while declaring no substantive change is correction-scope
overreach. An unresolved correction target is not accepted.

Corrections preserve the original response. They do not erase it or transfer identity,
incumbency, authority, or hidden memory.

## Role-specific content

The base `content` field may carry the analysis appropriate to the registered role.
Conformance does not standardize analytical style or private reasoning. The optional
conformance-examination profile supplies scenario coordinates for structured testing while
allowing `authority_analysis` to retain role-specific structure.

## Human control plane rendering

Humans do not need to inspect raw structured data. Render a response with:

```text
alvorada render-response response.json
```

The view displays the response identifier, member, canonical role, identity status, message
type, permitted output class, antecedent, envelope result, identity result, state effect, and
the explicit statement
`Substantive review: REQUIRES HUMAN / ROLE REVIEW`. Machine identifiers remain unchanged
where their established code is required.

Validate the same response with:

```text
alvorada validate-response response.json
```

For corrections, provide a directory containing preserved target responses:

```text
alvorada validate-response correction.json --responses responses/
```
