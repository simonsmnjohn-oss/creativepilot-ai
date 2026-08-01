# CreativePilot AI

A compliance-first LinkedIn referral outreach assistant. The app accepts user-supplied prospect data and a goal prompt, then drafts personalized connection notes and referral follow-up messages for manual review.

## Safety boundaries

This project intentionally does **not** scrape LinkedIn, automate credentialed browsing, bypass access controls, or auto-send connection requests/messages. Use it only with contacts you are allowed to contact, personalize every draft, and respect opt-outs and platform terms.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python -m creativepilot_ai.app
```

## API

### `POST /outreach/drafts`

Generates manual-review outreach drafts from user-provided prospects.

```json
{
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
      "shared_context": "we both attended a recent accessibility webinar"
    }
  ]
}
```

## Test

```bash
pytest
```
