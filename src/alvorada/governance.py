from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

THREE_LETTER_ACRONYM = re.compile(r"\b[A-Z]{3}\b")
WORD = re.compile(r"[A-Za-z]+")
VALID_UNKNOWN_STATES = {"UNKNOWN", "UNRESOLVED", "DISPUTED", "NOT TESTED", "INAPPLICABLE"}
AUTHORITY_EVENT_SCOPES = {
    "ADJUDICATION": "adjudicate",
    "AUTHORIZATION": "authorize",
    "EXECUTION": "execute",
    "CERTIFICATION": "certify",
}
REFERENCE_TARGETS = {
    "authority_sources": ("authorities", "delegations"),
    "authorities": ("authorities",),
    "offices": ("offices",),
    "delegations": ("delegations",),
    "active_missions": ("missions",),
}
EMERGENCY_IMMUTABLE_FIELDS = {"trigger", "scope", "duration", "authority_source"}


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str
    record_id: str | None = None


def _finding(severity: str, code: str, message: str, record: dict[str, Any]) -> Finding:
    record_id = (
        record.get("rule_id")
        or record.get("event_id")
        or record.get("mission_id")
        or record.get("office_id")
    )
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


def _grant_is_current(record: dict[str, Any], as_of: datetime) -> bool:
    expiry = _parse_time(record.get("expiry"))
    return _active(record) and (expiry is None or expiry >= as_of)


def _record_id(record: dict[str, Any]) -> str | None:
    value = (
        record.get("rule_id")
        or record.get("event_id")
        or record.get("office_id")
        or record.get("mission_id")
    )
    return str(value) if value else None


def _actor_for_grant(record: dict[str, Any]) -> str | None:
    value = (
        record.get("grantee") if record.get("rule_type") == "delegation" else record.get("holder")
    )
    return str(value) if value else None


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
        foundational = record.get("authority_basis") == "FOUNDATIONAL"
        if foundational:
            if source:
                findings.append(
                    _finding(
                        "ERROR",
                        "FOUNDATIONAL_AUTHORITY_HAS_UPSTREAM_SOURCE",
                        "A foundational authority claim cannot manufacture an upstream source.",
                        record,
                    )
                )
            if record.get("holder_type") != "human" or record.get("rule_type") != "authority":
                findings.append(
                    _finding(
                        "ERROR",
                        "INVALID_FOUNDATIONAL_AUTHORITY_CLAIM",
                        "Only an authority record for a human may represent "
                        "foundational authority.",
                        record,
                    )
                )
            provenance = record.get("provenance")
            if not isinstance(provenance, dict):
                findings.append(
                    _finding(
                        "ERROR",
                        "BROKEN_PROVENANCE",
                        "A foundational authority claim must preserve provenance.",
                        record,
                    )
                )
            elif provenance.get("status") == "DOCUMENTED":
                basis = record.get("foundational_basis")
                evidence = basis.get("evidence", []) if isinstance(basis, dict) else []
                has_evidence = isinstance(evidence, list) and any(
                    isinstance(item, str) and bool(item.strip()) for item in evidence
                )
                artifact = provenance.get("artifact")
                has_artifact = isinstance(artifact, str) and bool(artifact.strip())
                if not has_evidence and not has_artifact:
                    findings.append(
                        _finding(
                            "ERROR",
                            "FOUNDATIONAL_DOCUMENTED_WITHOUT_EVIDENCE",
                            "Documented foundational provenance requires supporting evidence "
                            "or an artifact reference.",
                            record,
                        )
                    )
            elif provenance.get("status") in {"UNKNOWN", "INCOMPLETE", "DISPUTED"}:
                findings.append(
                    _finding(
                        "WARNING",
                        "FOUNDATIONAL_PROVENANCE_UNVERIFIED",
                        "The foundational authority claim preserves unknown, incomplete, "
                        "or disputed provenance.",
                        record,
                    )
                )
            continue

        if not source or (
            source not in by_id and source not in document.get("external_authorities", [])
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
            missing = [
                field
                for field in (
                    "trigger",
                    "expiry",
                    "review_path",
                    "termination_condition",
                    "self_extension",
                )
                if not delegation.get(field)
            ]
            if missing:
                findings.append(
                    _finding(
                        "ERROR",
                        "INCOMPLETE_EMERGENCY_DELEGATION",
                        f"Emergency delegation lacks: {', '.join(missing)}.",
                        delegation,
                    )
                )
            if not parent or not _grant_is_current(parent, as_of):
                findings.append(
                    _finding(
                        "ERROR",
                        "EMERGENCY_WITHOUT_ACTIVE_AUTHORITY",
                        "Emergency delegation lacks valid active upstream authority.",
                        delegation,
                    )
                )
            elif not _scope(delegation).issubset(_scope(parent)):
                findings.append(
                    _finding(
                        "ERROR",
                        "EMERGENCY_SCOPE_EXCEEDED",
                        "Emergency authority exceeds its source scope.",
                        delegation,
                    )
                )
            amendable = {str(field) for field in delegation.get("amendable_fields", [])}
            if amendable & EMERGENCY_IMMUTABLE_FIELDS:
                findings.append(
                    _finding(
                        "ERROR",
                        "EMERGENCY_SELF_REDEFINITION",
                        "Emergency authority cannot redefine its trigger, scope, "
                        "duration, or source.",
                        delegation,
                    )
                )
            if delegation.get("self_extension") == "SEPARATELY_AUTHORIZED":
                extension = grants.get(str(delegation.get("extension_authority_source")))
                if (
                    not extension
                    or extension is delegation
                    or not _grant_is_current(extension, as_of)
                    or "extend_emergency" not in _scope(extension)
                ):
                    findings.append(
                        _finding(
                            "ERROR",
                            "UNAUTHORIZED_EMERGENCY_EXTENSION",
                            "Emergency extension lacks separate active authority.",
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
        if (
            not source
            or not _grant_is_current(source, as_of)
            or "create_mission" not in _scope(source)
        ):
            findings.append(
                _finding(
                    "ERROR",
                    "MISSION_WITHOUT_AUTHORITY",
                    "Mission creation lacks an active grant with create_mission scope.",
                    mission,
                )
            )


def _event_authority_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    as_of = _parse_time(document.get("as_of")) or datetime.now(UTC)
    grants = {
        str(record.get("rule_id")): record
        for record in [*document.get("authorities", []), *document.get("delegations", [])]
        if record.get("rule_id")
    }
    for event in document.get("events", []):
        required_scope = AUTHORITY_EVENT_SCOPES.get(str(event.get("event_type")))
        if not required_scope:
            continue
        if not _has_provenance(event):
            findings.append(
                _finding(
                    "ERROR",
                    "EVENT_BROKEN_PROVENANCE",
                    "An authority-exercising event must preserve provenance.",
                    event,
                )
            )
        source = grants.get(str(event.get("authority_source")))
        if not source:
            findings.append(
                _finding(
                    "ERROR",
                    "EVENT_WITHOUT_AUTHORITY",
                    "The event does not reference an existing authority source.",
                    event,
                )
            )
            continue
        if not _grant_is_current(source, as_of):
            findings.append(
                _finding(
                    "ERROR",
                    "EVENT_WITHOUT_ACTIVE_AUTHORITY",
                    "The event authority source is inactive or expired.",
                    event,
                )
            )
        if _actor_for_grant(source) != str(event.get("actor")):
            findings.append(
                _finding(
                    "ERROR",
                    "EVENT_ACTOR_NOT_ENTITLED",
                    "The event actor is not the holder or grantee of the authority source.",
                    event,
                )
            )
        scope_value = event.get("event_scope", [])
        event_scope = (
            {str(item) for item in scope_value} if isinstance(scope_value, list) else set()
        )
        if required_scope not in _scope(source) or not event_scope.issubset(_scope(source)):
            findings.append(
                _finding(
                    "ERROR",
                    "EVENT_SCOPE_EXCEEDS_AUTHORITY",
                    "The event function or scope exceeds its authority source.",
                    event,
                )
            )


def _lineage_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    records = [
        *document.get("authorities", []),
        *document.get("delegations", []),
        *document.get("offices", []),
        *document.get("events", []),
        *document.get("rules", []),
    ]
    ids = {identifier for record in records if (identifier := _record_id(record))}
    definitions: dict[str, str] = {}
    for record in records:
        replaces = record.get("replaces", [])
        replacement_ids = [replaces] if isinstance(replaces, str) else replaces
        lineage = [
            *record.get("supersedes", []),
            *replacement_ids,
            *record.get("governance_dependencies", []),
        ]
        for predecessor in lineage:
            if str(predecessor) not in ids:
                findings.append(
                    _finding(
                        "ERROR",
                        "BROKEN_LINEAGE",
                        f"Superseded record {predecessor!r} is missing.",
                        record,
                    )
                )
        if replacement_ids and not set(map(str, replacement_ids)).issubset(
            set(map(str, record.get("supersedes", [])))
        ):
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
    functions: dict[str, dict[str, set[str]]] = {}
    for event in document.get("events", []):
        subject = str(event.get("subject", ""))
        event_type = str(event.get("event_type", ""))
        actor = str(event.get("actor", ""))
        functions.setdefault(subject, {}).setdefault(event_type, set()).add(actor)

    pairs = [
        ("PROPOSAL", "AUTHORIZATION", "PROPOSAL_AUTHORIZATION_COLLAPSE"),
        ("ADJUDICATION", "AUTHORIZATION", "ADJUDICATION_AUTHORIZATION_COLLAPSE"),
        ("INSPECTION", "CERTIFICATION", "INSPECTION_CERTIFICATION_COLLAPSE"),
    ]
    for subject, actors in functions.items():
        for left, right, code in pairs:
            shared = actors.get(left, set()) & actors.get(right, set())
            for actor in sorted(shared):
                findings.append(
                    Finding(
                        "WARNING",
                        code,
                        f"{left.title()} and {right.lower()} share actor {actor!r}.",
                        subject,
                    )
                )
        participating_actors = set().union(*actors.values()) if actors else set()
        if len(actors) >= 4 and len(participating_actors) == 1:
            findings.append(
                Finding(
                    "WARNING",
                    "EXCESSIVE_FUNCTION_CONCENTRATION",
                    "Four or more governance functions are concentrated in one actor.",
                    subject,
                )
            )


def _acronym_is_expanded(text: str, match: re.Match[str]) -> bool:
    if match.start() == 0 or text[match.start() - 1] != "(":
        return False
    if match.end() >= len(text) or text[match.end()] != ")":
        return False
    words = WORD.findall(text[: match.start() - 1])
    acronym = match.group()
    return len(words) >= 3 and "".join(word[0].upper() for word in words[-3:]) == acronym


def _reference_checks(document: dict[str, Any], findings: list[Finding]) -> None:
    state = document.get("institutional_state")
    if not isinstance(state, dict):
        return
    for field, collections in REFERENCE_TARGETS.items():
        known = {
            identifier
            for collection in collections
            for record in document.get(collection, [])
            if (identifier := _record_id(record))
        }
        for reference in state.get(field, []):
            if not isinstance(reference, dict):
                continue
            if reference.get("resolution") == "RESOLVED" and str(reference.get("id")) not in known:
                findings.append(
                    _finding(
                        "ERROR",
                        "FALSELY_RESOLVED_REFERENCE",
                        f"State reference {reference.get('id')!r} is not locally resolved.",
                        reference,
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
        content = str(text.get("text", ""))
        unexplained = sorted(
            {
                match.group()
                for match in THREE_LETTER_ACRONYM.finditer(content)
                if not _acronym_is_expanded(content, match)
            }
        )
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
    if document.get("formal_authority") is not None or document.get("effective_power") is not None:
        findings.append(
            Finding(
                "INFORMATIONAL",
                "EXPERIMENTAL_EFFECTIVE_POWER_PLACEHOLDER",
                "The formal/effective comparison is a placeholder, not effective-power analysis.",
            )
        )


def validate_governance(document: dict[str, Any]) -> dict[str, Any]:
    """Return transparent findings; warnings and information do not make validation fail."""
    findings: list[Finding] = []
    _authority_checks(document, findings)
    _state_checks(document, findings)
    _event_authority_checks(document, findings)
    _lineage_checks(document, findings)
    _separation_checks(document, findings)
    _reference_checks(document, findings)
    _warning_and_information_checks(document, findings)
    serialized = [asdict(finding) for finding in findings]
    return {
        "valid": not any(finding.severity == "ERROR" for finding in findings),
        "errors": [item for item in serialized if item["severity"] == "ERROR"],
        "warnings": [item for item in serialized if item["severity"] == "WARNING"],
        "informational": [item for item in serialized if item["severity"] == "INFORMATIONAL"],
    }
