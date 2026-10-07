#!/usr/bin/env python3
"""Offline structural checks. Does NOT verify science, citations, policies or submission."""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any
if os.name == 'nt':
    _script_dir = os.path.abspath(os.path.dirname(__file__))
    if not _script_dir.startswith('\\\\?\\'):
        _script_dir = ('\\\\?\\UNC\\' + _script_dir[2:] if _script_dir.startswith('\\\\')
                       else '\\\\?\\' + _script_dir)
    sys.path.insert(0, _script_dir)
from path_utils import io_path
from local_files import check_local_file, file_hash, workspace_file_path

STAGES = {"intake", "topic", "ideation", "design", "execution", "analysis", "supplement", "writing", "review", "submission", "rebuttal"}
TYPES = {"method", "diagnostic", "empirical", "theory", "dataset", "systems"}
CHECKS = {"main_text_length", "template_version", "anonymity", "pdf_visual_review", "citations",
          "ai_policy", "ethics_and_data", "dual_submission", "authors", "submission_metadata", "supplementary"}

def nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def is_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in {"https", "http"} and bool(parsed.netloc)
    except ValueError:
        return False

def one_of(value: Any, choices: set[str]) -> bool:
    return isinstance(value, str) and value in choices

def validate(directory: Path, stage: str | None = None, baseline: Path | None = None,
             as_of: date | None = None) -> dict[str, Any]:
    directory = io_path(directory)
    today = as_of or date.today()
    errors: list[str] = []
    warnings: list[str] = []

    def read(name: str | Path) -> dict[str, Any]:
        path = io_path(name) if isinstance(name, Path) else directory / name
        try:
            # A Path is an explicitly requested baseline, which may be outside
            # the project; fixed workspace record names must stay inside it.
            if isinstance(name, str):
                path = workspace_file_path(directory, name)
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("JSON root must be an object")
            return value
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            return {}

    def obj(value: Any, label: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            errors.append(f"{label}: expected object")
            return {}
        return value

    def sequence(value: Any, label: str) -> list[Any]:
        if not isinstance(value, list):
            errors.append(f"{label}: expected array")
            return []
        return value

    def required(value: Any, label: str) -> None:
        if not nonblank(value):
            errors.append(f"{label}: nonempty text required")

    def dated(value: Any, label: str, same_day: bool = False) -> None:
        try:
            parsed = date.fromisoformat(value)
            if parsed > today:
                errors.append(f"{label}: cannot be a future verification date")
            if same_day and parsed != today:
                errors.append(f"{label}: final preflight needs a same-day policy check record ({today})")
        except (TypeError, ValueError):
            errors.append(f"{label}: expected YYYY-MM-DD")

    def local_file(value: Any, label: str, digest: Any = None, require_hash: bool = False) -> None:
        errors.extend(f"{label}: {issue}" for issue in
                      check_local_file(directory, value, digest, require_hash))

    project = read("project.json")
    ledger = read("evidence_ledger.json")
    active = stage or project.get("stage")
    if not one_of(active, STAGES):
        errors.append("stage: unsupported or missing")
    for key in (("project_id",) if active == "intake" else ("project_id", "user_request_verbatim") if active == "topic" else ("project_id", "user_request_verbatim", "research_question")):
        required(project.get(key), f"project.{key}")
    if not one_of(project.get("contribution_type"), TYPES):
        errors.append("project.contribution_type: unsupported or missing")
    obj(project.get("constraints"), "project.constraints")
    decisions = obj(project.get("author_decisions"), "project.author_decisions")
    for field in ("direction_approved", "submission_approved"):
        if not isinstance(decisions.get(field), bool):
            errors.append(f"author_decisions.{field}: expected boolean")
    if decisions.get("direction_approved") is not True:
        warnings.append("Scientific direction remains unconfirmed; do not imply author approval.")
    if active == "design":
        required(project.get("core_claim"), "project.core_claim")
        plan = obj(project.get("falsification_plan"), "project.falsification_plan")
        for field in ("minimal_experiment", "negative_control", "observation_that_would_weaken_claim"):
            required(plan.get(field), f"falsification_plan.{field}")

    sources: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(sequence(ledger.get("sources"), "ledger.sources")):
        source = obj(entry, f"sources[{index}]")
        sid = source.get("source_id")
        if not nonblank(sid):
            errors.append(f"sources[{index}]: source_id required")
            continue
        if sid in sources:
            errors.append(f"duplicate source_id: {sid}")
        sources[sid] = source
        if not one_of(source.get("kind"), {"public_paper", "local_result", "author_statement"}):
            errors.append(f"{sid}: unsupported source kind")
        if not one_of(source.get("verification"), {"unread", "read", "author_confirmed"}):
            errors.append(f"{sid}: unsupported verification")
        required(source.get("locator"), f"{sid}.locator")
        required(source.get("location_detail"), f"{sid}.location_detail")
        if one_of(source.get("verification"), {"read", "author_confirmed"}):
            dated(source.get("checked_on"), f"{sid}.checked_on")
        if source.get("kind") == "public_paper" and not is_url(source.get("locator")):
            errors.append(f"{sid}: public paper requires an HTTP(S) source URL")
        if source.get("kind") == "local_result":
            local_file(source.get("locator"), sid, source.get("sha256"), active == "submission")

    seen: set[str] = set()
    claims = sequence(ledger.get("claims"), "ledger.claims")
    for index, entry in enumerate(claims):
        claim = obj(entry, f"claims[{index}]")
        cid = claim.get("claim_id")
        if not nonblank(cid):
            errors.append(f"claims[{index}]: claim_id required")
            continue
        if cid in seen:
            errors.append(f"duplicate claim_id: {cid}")
        seen.add(cid)
        required(claim.get("text"), f"{cid}.text")
        if not one_of(claim.get("claim_type"), {"hypothesis", "empirical", "literature", "theoretical", "method"}):
            errors.append(f"{cid}: unsupported claim_type")
        if not one_of(claim.get("use_in_manuscript"), {"planned", "background", "method", "reported_result"}):
            errors.append(f"{cid}: unsupported use_in_manuscript")
        if not one_of(claim.get("status"), {"proposed", "supported", "author_confirmed"}):
            errors.append(f"{cid}: unsupported status")
        ids = sequence(claim.get("evidence_ids"), f"{cid}.evidence_ids")
        resolved = []
        for sid in ids:
            if not isinstance(sid, str) or sid not in sources:
                errors.append(f"{cid}: unknown evidence source: {sid!r}")
            else:
                resolved.append(sources[sid])
        if claim.get("use_in_manuscript") == "reported_result":
            if claim.get("claim_type") == "hypothesis" or claim.get("status") == "proposed":
                errors.append(f"{cid}: a hypothesis/proposed claim cannot be a reported result")
        needs_support = one_of(claim.get("status"), {"supported", "author_confirmed"}) or claim.get("use_in_manuscript") == "reported_result"
        if needs_support:
            if not ids:
                errors.append(f"{cid}: supporting source required")
            if any(not one_of(s.get("verification"), {"read", "author_confirmed"}) for s in resolved):
                errors.append(f"{cid}: supporting source has not been read or author-confirmed")
        if "scope" in claim:
            obj(claim["scope"], f"{cid}.scope")

    novelty = obj(project.get("novelty_assessment"), "project.novelty_assessment")
    if not one_of(novelty.get("status"), {"not_assessed", "insufficient_search", "overlap_found", "differentiated", "needs_revision"}):
        errors.append("novelty_assessment.status: unsupported value")
    if novelty.get("status") == "differentiated":
        required(novelty.get("delta"), "novelty_assessment.delta")
        local_file(novelty.get("search_log"), "novelty_assessment.search_log")
        nearest = sequence(novelty.get("closest_prior_ids"), "novelty_assessment.closest_prior_ids")
        if not nearest:
            errors.append("Differentiation requires a closest-prior comparison; zero results are not novelty.")
        for sid in nearest:
            source = sources.get(sid, {}) if isinstance(sid, str) else {}
            if source.get("kind") != "public_paper" or source.get("verification") != "read":
                errors.append(f"novelty: closest work {sid!r} needs a read public-paper record")
    else:
        warnings.append("Novelty is not structurally documented as differentiated; do not claim it is verified.")

    if baseline is not None:
        previous = read(io_path(baseline))
        for key in ("research_question", "constraints", "core_claim", "falsification_plan"):
            if previous.get(key) != project.get(key):
                errors.append(f"baseline change in {key}: obtain renewed author confirmation and redo affected checks")

    if active == "submission":
        venue = read("venue_profile.json")
        target = obj(project.get("target_venue"), "project.target_venue")
        for field, target_field in (("conference", "name"), ("year", "year"), ("track", "track")):
            value = venue.get(field)
            if value is None or value == "":
                errors.append(f"venue.{field}: required")
            if value != target.get(target_field):
                errors.append(f"venue.{field}: does not match project target")
        if not isinstance(venue.get("year"), int) or isinstance(venue.get("year"), bool):
            errors.append("venue.year: integer required")
        if not one_of(venue.get("submission_stage"), {"initial", "revision", "camera_ready", "rebuttal"}):
            errors.append("venue.submission_stage: unsupported")
        dated(venue.get("checked_on"), "venue.checked_on", same_day=True)
        policies = sequence(venue.get("official_sources"), "venue.official_sources")
        known_urls: set[str] = set()
        if not policies:
            errors.append("venue.official_sources: actual policy source records required")
        for index, value in enumerate(policies):
            policy = obj(value, f"official_sources[{index}]")
            if not is_url(policy.get("url")):
                errors.append(f"official_sources[{index}]: valid source URL required")
            else:
                known_urls.add(policy["url"])
            required(policy.get("location_detail"), f"official_sources[{index}].location_detail")
            dated(policy.get("checked_on"), f"official_sources[{index}].checked_on", same_day=True)
        deadlines = sequence(venue.get("deadlines"), "venue.deadlines")
        if not deadlines:
            errors.append("venue.deadlines: record the applicable stage deadline with a timezone")
        for index, value in enumerate(deadlines):
            deadline = obj(value, f"deadlines[{index}]")
            required(deadline.get("name"), f"deadlines[{index}].name")
            required(deadline.get("original_text"), f"deadlines[{index}].original_text")
            if not isinstance(deadline.get("source_url"), str) or deadline['source_url'] not in known_urls:
                errors.append(f"deadlines[{index}]: source must be in official_sources")
            try:
                parsed = datetime.fromisoformat(deadline.get("datetime"))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    raise ValueError("timezone missing")
                if parsed.date() < today:
                    warnings.append(f"deadlines[{index}]: recorded deadline has passed; do not imply submission remains open.")
            except (ValueError, TypeError):
                errors.append(f"deadlines[{index}]: valid ISO timestamp with UTC offset required")
        observed: set[str] = set()
        for index, value in enumerate(sequence(venue.get("checks"), "venue.checks")):
            check = obj(value, f"checks[{index}]")
            cid = check.get("id")
            if not nonblank(cid):
                errors.append(f"checks[{index}]: id required")
                continue
            if cid in observed:
                errors.append(f"duplicate venue check: {cid}")
            observed.add(cid)
            if not one_of(check.get("status"), {"pass", "not_applicable"}):
                errors.append(f"venue check {cid}: unresolved/failed")
            required(check.get("detail"), f"venue check {cid}.detail")
            required(check.get("evidence"), f"venue check {cid}.evidence")
            if check.get("source_url") is not None and (not isinstance(check['source_url'], str) or check['source_url'] not in known_urls):
                errors.append(f"venue check {cid}: source must be in official_sources")
        for cid in sorted(CHECKS - observed):
            errors.append(f"venue check missing: {cid}")
        if venue.get("manual_preflight_completed") is not True:
            errors.append("manual_preflight_completed must be explicitly recorded")
        artifacts = sequence(venue.get("prepared_artifacts"), "venue.prepared_artifacts")
        if not artifacts:
            errors.append("No prepared artifact files recorded")
        for index, value in enumerate(artifacts):
            artifact = obj(value, f"prepared_artifacts[{index}]")
            local_file(artifact.get("path"), f"artifact[{index}]", artifact.get("sha256"), True)
        if not claims:
            errors.append("Final preflight needs a core claim–evidence inventory (empirical or theoretical).")
        warnings.append("Policy URLs and human-check flags are declarations, not independently verified by this script.")

    return {
        "workspace": str(directory), "stage": active, "as_of": today.isoformat(),
        "structural_status": "pass" if not errors else "needs_attention",
        "scientific_verification": "not_performed", "online_policy_verification": "not_performed",
        "submission_action": "not_performed", "errors": errors, "warnings": warnings,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--stage", choices=sorted(STAGES))
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, help="Explicit validation date; historical values are for reproducible tests, not current readiness.")
    args = parser.parse_args()
    try:
        report = validate(args.workspace, args.stage, args.baseline, args.as_of)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"structural_status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["structural_status"] == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
