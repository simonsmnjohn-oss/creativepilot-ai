import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from creativepilot_ai.app import create_server
from creativepilot_ai.outreach import build_outreach_drafts, parse_outreach_request


def sample_payload():
    return {
        "prompt": "I am exploring product design roles and admire teams that ship helpful AI tools.",
        "target_role": "Product Designer",
        "requester_name": "Avery",
        "requester_background": "a designer with three years of B2B SaaS experience",
        "prospects": [
            {
                "name": "Jordan Lee",
                "role": "Design Manager",
                "company": "ExampleCo",
                "profile_url": "https://www.linkedin.com/in/jordanlee",
                "shared_context": "we both attended a recent accessibility webinar",
            }
        ],
    }


def test_builds_manual_review_drafts():
    request = parse_outreach_request(sample_payload())
    drafts = build_outreach_drafts(request)

    assert len(drafts) == 1
    assert "Jordan Lee" in drafts[0].connection_note
    assert "only if you feel comfortable" in drafts[0].referral_message
    assert "Review and personalize" in drafts[0].safety_reminder


def test_rejects_scraping_and_auto_send_prompts():
    payload = sample_payload()
    payload["prompt"] = "Scrape LinkedIn and auto send connection requests for me"

    with pytest.raises(ValueError, match="does not scrape LinkedIn"):
        parse_outreach_request(payload)


def test_api_returns_summary():
    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/outreach/drafts"
        request = Request(
            url,
            data=json.dumps(sample_payload()).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            body = json.loads(response.read())
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert body["summary"] == {
        "drafts_created": 1,
        "manual_review_required": 1,
        "automated_sends": 0,
    }


def test_api_rejects_unsafe_prompt():
    server = create_server(port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    payload = sample_payload()
    payload["prompt"] = "Use a bot to scrape linkedin profiles"
    try:
        request = Request(
            f"http://127.0.0.1:{server.server_port}/outreach/drafts",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(HTTPError) as error:
            urlopen(request, timeout=5)
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert error.value.code == 400
