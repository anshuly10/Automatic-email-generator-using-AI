# drafter.py
import json
import re
import ollama

MODEL = "llama3.2"

def draft_email(
    recipients: list[str],
    purpose: str,
    context: str,
    tone: str,
    sender_name: str = "",
    attachment_name: str = "",
) -> dict:
    attachment_note = (
        f'\nThe email should naturally mention an attached file named "{attachment_name}".'
        if attachment_name else ""
    )

    prompt = f"""You are an expert email writer. Draft a SHORT and {tone} email. Be concise, maximum 250 words in the body.

Recipients: {", ".join(recipients)}
Purpose / Subject: {purpose}
Key points: {context}{attachment_note}
{"Sign off as: " + sender_name if sender_name else ""}

Respond ONLY with this exact JSON (no markdown, no code fences, no extra text):
{{"subject": "subject line here", "body": "email body here"}}

Keep the body under 250 words. Put the entire body on one line inside the JSON."""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={
        "num_predict": 2048,
        "temperature": 0.7,
    }
    )

    raw = response["message"]["content"].strip()

    print("DEBUG RAW:", repr(raw))
    '''
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Unexpected response format:\n{raw[:300]}")
  '''

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try extracting JSON block
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                # JSON is truncated — extract subject and body manually
                subject_match = re.search(r'"subject"\s*:\s*"([^"]+)"', raw)
                body_match = re.search(r'"body"\s*:\s*"([\s\S]+?)(?:"\s*\}|$)', raw)
                if subject_match and body_match:
                    return {
                        "subject": subject_match.group(1),
                        "body": body_match.group(1).replace('\\n', '\n')
                    }
        raise ValueError(f"Unexpected response format:\n{raw[:300]}")      