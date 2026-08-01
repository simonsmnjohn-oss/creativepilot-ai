from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable
from urllib.parse import urlparse

BANNED_AUTOMATION_TERMS = (
    "auto send",
    "autosend",
    "scrape linkedin",
    "scraping linkedin",
    "bypass",
    "cookie",
    "credentials",
    "bot",
)


@dataclass(frozen=True)
class Prospect:
    """A prospect supplied by the user from an owned list or manual research."""

    name: str
    role: str
    company: str
    profile_url: str | None = None
    shared_context: str = ""


@dataclass(frozen=True)
class OutreachRequest:
    prompt: str
    target_role: str
    requester_name: str
    requester_background: str
    prospects: list[Prospect]


@dataclass(frozen=True)
class OutreachDraft:
    prospect: Prospect
    connection_note: str
    referral_message: str
    safety_reminder: str


def parse_outreach_request(payload: dict) -> OutreachRequest:
    """Validate JSON-compatible payloads for the outreach drafting API."""

    prompt = _required_text(payload, "prompt", 8, 1200)
    lowered = prompt.lower()
    for term in BANNED_AUTOMATION_TERMS:
        if term in lowered:
            raise ValueError(
                "This assistant drafts manual, consent-respecting outreach only; "
                "it does not scrape LinkedIn, bypass access controls, or auto-send messages."
            )

    raw_prospects = payload.get("prospects")
    if not isinstance(raw_prospects, list) or not 1 <= len(raw_prospects) <= 25:
        raise ValueError("prospects must contain 1 to 25 items")

    prospects = [_parse_prospect(item) for item in raw_prospects]
    return OutreachRequest(
        prompt=prompt,
        target_role=_required_text(payload, "target_role", 1, 160),
        requester_name=_required_text(payload, "requester_name", 1, 120),
        requester_background=_required_text(payload, "requester_background", 1, 600),
        prospects=prospects,
    )


def build_outreach_drafts(request: OutreachRequest) -> list[OutreachDraft]:
    """Create review-required connection and referral drafts for supplied prospects."""

    return [_build_single_draft(request, prospect) for prospect in request.prospects]


def serialize_draft(draft: OutreachDraft) -> dict:
    serialized = asdict(draft)
    return serialized


def summarize_pipeline(drafts: Iterable[OutreachDraft]) -> dict[str, int]:
    drafts = list(drafts)
    return {
        "drafts_created": len(drafts),
        "manual_review_required": len(drafts),
        "automated_sends": 0,
    }


def _parse_prospect(payload: object) -> Prospect:
    if not isinstance(payload, dict):
        raise ValueError("each prospect must be an object")
    profile_url = payload.get("profile_url")
    if profile_url is not None:
        profile_url = _required_text(payload, "profile_url", 8, 300)
        parsed = urlparse(profile_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("profile_url must be a valid HTTP URL")
    return Prospect(
        name=_required_text(payload, "name", 1, 120),
        role=_required_text(payload, "role", 1, 160),
        company=_required_text(payload, "company", 1, 160),
        profile_url=profile_url,
        shared_context=_optional_text(payload, "shared_context", 500),
    )


def _required_text(payload: dict, key: str, min_length: int, max_length: int) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    value = re.sub(r"\s+", " ", value.strip())
    if not min_length <= len(value) <= max_length:
        raise ValueError(f"{key} must be between {min_length} and {max_length} characters")
    return value


def _optional_text(payload: dict, key: str, max_length: int) -> str:
    value = payload.get(key, "")
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    value = re.sub(r"\s+", " ", value.strip())
    if len(value) > max_length:
        raise ValueError(f"{key} must be no more than {max_length} characters")
    return value


def _clean_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    return text[:1].upper() + text[1:] if text else text


def _build_single_draft(request: OutreachRequest, prospect: Prospect) -> OutreachDraft:
    context = _clean_sentence(prospect.shared_context)
    opener = f"Hi {prospect.name}, I noticed your work as {article(prospect.role)} {prospect.role} at {prospect.company}."
    if context:
        opener += f" {context}."

    connection_note = (
        f"{opener} I'm {request.requester_name}, {request.requester_background}. "
        f"I'd be grateful to connect and learn from your experience around {request.target_role}."
    )

    referral_message = (
        f"Hi {prospect.name}, thanks for connecting. {request.prompt} "
        f"Given your perspective at {prospect.company}, would you be open to a brief conversation "
        f"or, only if you feel comfortable, pointing me toward the right referral path for {request.target_role}?"
    )

    return OutreachDraft(
        prospect=prospect,
        connection_note=connection_note,
        referral_message=referral_message,
        safety_reminder=(
            "Review and personalize before sending. Contact only people you have a legitimate reason "
            "to reach, honor opt-outs, and use LinkedIn manually in line with its terms."
        ),
    )


def article(word: str) -> str:
    return "an" if word[:1].lower() in {"a", "e", "i", "o", "u"} else "a"
