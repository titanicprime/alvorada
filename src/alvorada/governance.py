from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

THREE_LETTER_ACRONYM = re.compile(r"\b[A-Z]{3}\b")
VALID_UNKNOWN_STATES = {"UNKNOWN", "UNRESOLVED", "DISPUTED", "NOT TESTED", "INAPPLICABLE"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    record_id: str | None = None


def _finding(severity: str, code: str, message: str, record: dict[str, Any]) -> Finding:
    record_id = record.get("rule_id") or record.get("mission_id") or record.get("office_id")
    return Finding(severity, code, message, str(record_id) if record_id else None)


def _active(record: dict[str, Any]) -> bool:
    return record.get("status") == "ACTIVE"


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _scope(record: dict[str, Any]) -> set[str]:
    value = record.get("scope", [])
    return {str(item) for item in value} if isinstance(value, list) else set()


def _has_provenance(record: dict[str, Any]) -> bool:
    provenance = record.get("provenance")
    return (
        isinstance(provenance, dict)
        and bool(provenance.get("artifact"))
        and bool(provenance.get("authorized_by"))
    )


def _authority_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    authorities = document.get("authorities", [])
    delegations = document.get("delegations", [])
    records = [*authorities, *delegations]
    identifier_records = [
        *records,
        *document.get("offices", []),
        *document.get("events", []),
        *document.get("rules", []),
        *document.get("claims", []),
        *document.get("human_texts", []),
    ]
    identifiers = [
        str(record.get("rule_id")) for record in identifier_records if record.get("rule_id")
    ]
    duplicates = {identifier for identifier, count in Counter(identifiers).items() if count > 1}
    for identifier in sorted(duplicates):
        findings.append(
            Finding(
                "ERROR",
                "DUPLICATE_RULE_ID",
                f"Rule identifier {identifier!r} is not unique.",
                identifier,
            )
        )
    by_id = {str(record.get("rule_id")): record for record in records if record.get("rule_id")}

    for record in records:
        source = record.get("authority_source")
        if (
            source
            and source not in by_id
            and source not in document.get("external_authorities", [])
        ):
            findings.append(
                _finding(
                    "ERROR",
                    "UNDEFINED_AUTHORITY",
                    f"Authority source {source!r} is not defined.",
                    record,
                )
            )
        if source == record.get("rule_id") or record.get("self_attested") is True:
            findings.append(
                _finding(
                    "ERROR",
                    "SELF_ATTESTED_AUTHORITY",
                    "A record cannot attest its own authority.",
                    record,
                )
            )
        if not _has_provenance(record):
            findings.append(
                _finding(
                    "ERROR",
                    "BROKEN_PROVENANCE",
                    "Authority provenance is incomplete.",
                    record,
                )
            )
        parent = by_id.get(str(source))
        if parent and not _scope(record).issubset(_scope(parent)):
            findings.append(
                _finding(
                    "ERROR",
                    "AUTHORITY_SCOPE_ENLARGEMENT",
                    "A grant exceeds the scope of its authority source.",
                    record,
                )
            )
        if (
            record.get("holder_type") == "artificial_intelligence"
            and record.get("foundational") is True
        ):
            findings.append(
                _finding(
                    "ERROR",
                    "ARTIFICIAL_FOUNDATIONAL_AUTHORITY",
                    "Artificial intelligence cannot claim foundational human authority.",
                    record,
                )
            )

    for delegation in delegations:
        parent = by_id.get(str(delegation.get("authority_source")))
        if (
            parent
            and parent.get("rule_type") == "delegation"
            and parent.get("subdelegation") != "PERMITTED"
        ):
            findings.append(
                _finding(
                    "ERROR",
                    "UNAUTHORIZED_SUBDELEGATION",
                    "Sub-delegation is not explicitly permitted by the source grant.",
                    delegation,
                )
            )

    graph: dict[str, set[str]] = {}
    for item in delegations:
        if item.get("grantor") and item.get("grantee"):
            graph.setdefault(str(item["grantor"]), set()).add(str(item["grantee"]))
    colors: dict[str, int] = {}
    cycle_detected = False
    for start in graph:
        if colors.get(start, 0) != 0:
            continue
        colors[start] = 1
        pending: list[tuple[str, Iterator[str]]] = [(start, iter(graph.get(start, set())))]
        while pending:
            node, children = pending[-1]
            try:
                target = next(children)
            except StopIteration:
                colors[node] = 2
                pending.pop()
                continue
            target_color = colors.get(target, 0)
            if target_color == 1:
                cycle_detected = True
            elif target_color == 0:
                colors[target] = 1
                pending.append((target, iter(graph.get(target, set()))))
    if cycle_detected:
        findings.append(
            Finding(
                "ERROR",
                "DELEGATION_CYCLE",
                "A delegation cycle exists.",
            )
        )


def _state_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    as_of = _parse_time(document.get("as_of")) or datetime.now(UTC)
    authorities = document.get("authorities", [])
    delegations = document.get("delegations", [])
    grants = {str(record.get("rule_id")): record for record in [*authorities, *delegations]}

    for delegation in delegations:
        expiry = _parse_time(delegation.get("expiry"))
        if _active(delegation) and expiry and expiry < as_of:
            findings.append(
                _finding(
                    "ERROR",
                    "EXPIRED_DELEGATION_ACTIVE",
                    "An expired delegation is treated as active.",
                    delegation,
                )
            )
        if delegation.get("emergency") is True:
            parent = grants.get(str(delegation.get("authority_source")))
            if parent and not _scope(delegation).issubset(_scope(parent)):
                findings.append(
                    _finding(
                        "ERROR",
                        "EMERGENCY_SCOPE_EXCEEDED",
                        "Emergency authority exceeds its source scope.",
                        delegation,
                    )
                )

    for office in document.get("offices", []):
        valid_scope: set[str] = set()
        for grant_id in office.get("grant_ids", []):
            grant = grants.get(str(grant_id))
            expiry = _parse_time(grant.get("expiry")) if grant else None
            if grant and _active(grant) and (expiry is None or expiry >= as_of):
                valid_scope |= _scope(grant)
        if not _scope(office).issubset(valid_scope):
            findings.append(
                _finding(
                    "ERROR",
                    "ROLE_AUTHORITY_EXCEEDS_GRANT",
                    "A role or office claims authority outside its valid grants.",
                    office,
                )
            )
        if office.get("implementation") == office.get("office_id"):
            findings.append(
                _finding(
                    "WARNING",
                    "ROLE_IMPLEMENTATION_COLLAPSE",
                    "A role or office is identified as its implementation.",
                    office,
                )
            )

    for mission in document.get("missions", []):
        source = grants.get(str(mission.get("authority_source")))
        if not source or "create_mission" not in _scope(source):
            findings.append(
                _finding(
                    "ERROR",
                    "MISSION_WITHOUT_AUTHORITY",
                    "Mission creation lacks an active grant with create_mission scope.",
                    mission,
                )
            )


def _lineage_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    records = document.get("rules", [])
    ids = {str(record.get("rule_id")) for record in records}
    definitions: dict[str, str] = {}
    for record in records:
        for predecessor in record.get("supersedes", []):
            if str(predecessor) not in ids:
                findings.append(
                    _finding(
                        "ERROR",
                        "BROKEN_LINEAGE",
                        f"Superseded record {predecessor!r} is missing.",
                        record,
                    )
                )
        if record.get("replaces") and not record.get("supersedes"):
            findings.append(
                _finding(
                    "ERROR",
                    "SILENT_SUPERSESSION",
                    "A replacement does not preserve explicit supersession lineage.",
                    record,
                )
            )
        term = record.get("term")
        definition = record.get("definition")
        if term and definition:
            prior = definitions.get(str(term))
            if prior is not None and prior != definition:
                findings.append(
                    _finding(
                        "WARNING",
                        "CONFLICTING_DEFINITIONS",
                        f"Conflicting definitions exist for {term!r}.",
                        record,
                    )
                )
            definitions[str(term)] = str(definition)


def _separation_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    functions: dict[str, dict[str, str]] = {}
    for event in document.get("events", []):
        subject = str(event.get("subject", ""))
        event_type = str(event.get("event_type", ""))
        actor = str(event.get("actor", ""))
        functions.setdefault(subject, {})[event_type] = actor

    pairs = [
        ("PROPOSAL", "AUTHORIZATION", "PROPOSAL_AUTHORIZATION_COLLAPSE"),
        ("ADJUDICATION", "AUTHORIZATION", "ADJUDICATION_AUTHORIZATION_COLLAPSE"),
        ("INSPECTION", "CERTIFICATION", "INSPECTION_CERTIFICATION_COLLAPSE"),
    ]
    for subject, actors in functions.items():
        for left, right, code in pairs:
            if actors.get(left) and actors.get(left) == actors.get(right):
                findings.append(
                    Finding(
                        "WARNING",
                        code,
                        f"{left.title()} and {right.lower()} share actor {actors[left]!r}.",
                        subject,
                    )
                )
        if len(actors) >= 4 and len(set(actors.values())) == 1:
            findings.append(
                Finding(
                    "WARNING",
                    "EXCESSIVE_FUNCTION_CONCENTRATION",
                    "Four or more governance functions are concentrated in one actor.",
                    subject,
                )
            )


def _warning_and_information_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    for claim in document.get("claims", []):
        if claim.get("prior_status") in VALID_UNKNOWN_STATES and not claim.get("evidence"):
            findings.append(
                _finding(
                    "WARNING",
                    "UNKNOWN_PROMOTED_WITHOUT_EVIDENCE",
                    "An unresolved state was promoted without evidence.",
                    claim,
                )
            )
    for text in document.get("human_texts", []):
        expanded = set(text.get("expanded_acronyms", []))
        acronyms = set(THREE_LETTER_ACRONYM.findall(str(text.get("text", ""))))
        unexplained = sorted(acronyms - expanded)
        if unexplained:
            findings.append(
                _finding(
                    "WARNING",
                    "UNEXPLAINED_THREE_LETTER_ACRONYM",
                    f"Unexplained three-letter acronyms: {', '.join(unexplained)}.",
                    text,
                )
            )
    for rule in document.get("rules", []):
        if rule.get("constitutional") is True and rule.get("layer") == "technical_standard":
            findings.append(
                _finding(
                    "WARNING",
                    "CONSTITUTION_ONLY_IN_TECHNICAL_STANDARD",
                    "A constitutional rule appears only in a technical standard.",
                    rule,
                )
            )
        if rule.get("rule_type") == "technical" and rule.get("constitutional") is True:
            findings.append(
                _finding(
                    "WARNING",
                    "TECHNICAL_RULE_ELEVATED",
                    "A technical rule is marked as constitutional law.",
                    rule,
                )
            )
        reversibility = rule.get("reversibility")
        if isinstance(reversibility, dict) and (
            not reversibility.get("formal") or not reversibility.get("practical")
        ):
            findings.append(
                _finding(
                    "WARNING",
                    "WEAK_REVERSIBILITY",
                    "Formal and practical reversibility are not both declared.",
                    rule,
                )
            )
        if rule.get("deprecated_terminology"):
            findings.append(
                _finding("INFORMATIONAL", "DEPRECATED_TERMINOLOGY", "Deprecated terminology.", rule)
            )
        if rule.get("historical_role_name"):
            findings.append(
                _finding("INFORMATIONAL", "HISTORICAL_ROLE_NAME", "Historical role name.", rule)
            )
        if rule.get("migration_opportunity"):
            findings.append(
                _finding("INFORMATIONAL", "MIGRATION_OPPORTUNITY", "Migration opportunity.", rule)
            )
        if rule.get("metadata_complete") is False:
            findings.append(
                _finding("INFORMATIONAL", "INCOMPLETE_METADATA", "Metadata is incomplete.", rule)
            )
    if document.get("documentation_drift"):
        findings.append(
            Finding(
                "INFORMATIONAL",
                "DOCUMENTATION_DRIFT",
                "Non-blocking documentation drift is recorded.",
            )
        )
    if document.get("formal_authority") != document.get("effective_power") and (
        document.get("formal_authority") is not None and document.get("effective_power") is not None
    ):
        findings.append(
            Finding(
                "WARNING",
                "FORMAL_EFFECTIVE_POWER_DIVERGENCE",
                "Material divergence exists between formal authority and effective power.",
            )
        )


def validate_governance(document: dict[str, Any]) -> dict[str, Any]:
    """Return transparent findings; warnings and information do not make validation fail."""
    findings: list[Finding] = []
    _authority_checks(document, findings)
    _state_checks(document, findings)
    _lineage_checks(document, findings)
    _separation_checks(document, findings)
    _warning_and_information_checks(document, findings)
    serialized = [asdict(finding) for finding in findings]
    return {
        "valid": not any(finding.severity == "ERROR" for finding in findings),
        "errors": [item for item in serialized if item["severity"] == "ERROR"],
        "warnings": [item for item in serialized if item["severity"] == "WARNING"],
        "informational": [item for item in serialized if item["severity"] == "INFORMATIONAL"],
    }
