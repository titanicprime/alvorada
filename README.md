
# Project Alvorada

Project Alvorada is a private experimental repository for developing machine-verifiable, lineage-preserving communication protocols between heterogeneous AI agents.

Project Alvorada hosts the canonical machine-readable artifacts for **ODEX-IMX**, an experimental interagent exchange profile that extends ODES design principles for deterministic state transfer, typed claims, explicit authority, semantic compression, and recoverable lineage.

## Why plain English alone is insufficient

Plain English is useful for explanation, but it is insufficient as the sole interagent transport when agents need deterministic state replay, canonical terminology, typed claims, compact codebooks, and machine-verifiable conformance. ODEX-IMX separates human explanation from authoritative machine-readable artifacts.

## Transport is not reasoning

ODEX-IMX transports structured coordinates about state, evidence, authority, lineage, and transformation. It does **not** transport private chain-of-thought, hidden reasoning traces, certification, truth, assurance, or regulatory recognition.

## Quick start

```bash
python -m pip install -e .[dev]
alvorada validate /absolute/path/to/examples/valid/mission.json
alvorada canonicalize /absolute/path/to/examples/valid/mission.json
alvorada hash /absolute/path/to/examples/valid/mission.json
alvorada verify-hash /absolute/path/to/examples/valid/mission.json
alvorada encode /absolute/path/to/examples/valid/mission.json --codebook /absolute/path/to/codebooks/protocol-codebook.json
alvorada decode /absolute/path/to/encoded.json --codebook /absolute/path/to/codebooks/protocol-codebook.json
alvorada apply-deltas /absolute/path/to/base.json /absolute/path/to/deltas.json
alvorada verify-lineage /absolute/path/to/examples/valid
alvorada dictionary-check
alvorada codebook-check
```

## Valid message example

```json
{
  "protocol": "ODEX-IMX",
  "version": "0.2",
  "header": {
    "message_id": "MSG-ACK-0001",
    "in_reply_to": "MSG-MISSION-0001",
    "from": "Blue-0",
    "to": "Red-1",
    "response_type": "ACK",
    "mission_id": "MISSION-ALV-001",
    "timestamp": "2026-07-16T01:00:00Z",
    "state_version": "state-v1"
  },
  "state": {"alignment": "PASS"},
  "delta": {"operations": [], "parent_state_hash": null, "lineage": []},
  "claims": [{"claim_id": "CLM-ACK-0001", "register": "DERIVED", "body": "Blue-0 confirms receipt of mission MISSION-ALV-001.", "authority_status": "LIMITED"}],
  "conflicts": [],
  "questions": [],
  "next_action": {"status": "READY", "owner": "Blue-0", "summary": "Begin mission execution."},
  "human_note": {"summary": "Receipt acknowledgement only; no truth claim is implied."},
  "integrity": {"sha256": "ad990630538a383822b86f562000846a02515a8784b22c8f97ee59fcde6efdbb"}
}
```

## Conformance levels

1. **SCHEMA_VALID** — JSON matches the authoritative schema.
2. **PROFILE_CONFORMANT** — JSON also satisfies a declared profile.
3. **VERIFIER_ACCEPTED** — a verifier accepts the artifact after machine checks.
4. **RELIED_UPON** — an external relying party decides to rely on it.

No lower level implies a higher level.

## Current maturity status

This repository is an MVP-quality private research substrate. It is intentionally narrow, append-oriented, and focused on deterministic validation rather than broad ecosystem integration.

## Limitations

- No digital signature support is implemented.
- Schema validity does not establish truth.
- Protocol conformance does not establish reliance.
- The repository does not provide a trust network, certification system, or product announcement.

## Private research status

Project Alvorada is private and experimental. Governance, authority examples, schemas, dictionaries, codebooks, and tests may evolve through explicit review and versioning only.
