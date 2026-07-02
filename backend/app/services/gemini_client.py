"""
app/services/gemini_client.py — LLM calls via Groq API (llama-3.1-8b-instant).
Groq free tier: 14,400 requests/day, 30 requests/min — much higher than Gemini.
"""

from __future__ import annotations

import asyncio

import httpx

_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_MODEL = "llama-3.1-8b-instant"


def _get_key() -> str:
    from app.core.config import get_settings
    return get_settings().groq_api_key


async def ask_llm(prompt: str, retries: int = 3) -> str:
    """Send a prompt to Groq and return the text response."""
    headers = {
        "Authorization": f"Bearer {_get_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2048,
    }
    for attempt in range(retries):
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(_GROQ_URL, json=payload, headers=headers)
            if resp.status_code == 429:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    raise RuntimeError("AI is busy right now. Please wait 30 seconds and try again.")


async def explain_concept(question: str, code: str | None = None) -> dict:
    """Ask the LLM to explain a Python concept and return a check question."""
    code_block = f"\n\nCode:\n```python\n{code}\n```" if code else ""
    prompt = f"""You are a friendly Python tutor. A student asked:

"{question}"{code_block}

Reply in this EXACT format with no extra text:

EXPLANATION:
<clear explanation in 3-5 sentences using simple language>

TOPIC:
<single topic name, e.g. "list comprehensions">

CHECK QUESTION:
<one short question to test understanding>"""

    raw = await ask_llm(prompt)
    return _parse_explanation(raw)


def _parse_explanation(raw: str) -> dict:
    result = {"explanation": "", "topic": "Python", "check_question": ""}
    current: str | None = None
    lines: list[str] = []

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("EXPLANATION:"):
            current = "explanation"
            lines = []
            rest = stripped[len("EXPLANATION:"):].strip()
            if rest:
                lines.append(rest)
        elif stripped.startswith("TOPIC:"):
            if current:
                result[current] = "\n".join(lines).strip()
            current = "topic"
            lines = []
            rest = stripped[len("TOPIC:"):].strip()
            if rest:
                lines.append(rest)
        elif stripped.startswith("CHECK QUESTION:"):
            if current:
                result[current] = "\n".join(lines).strip()
            current = "check_question"
            lines = []
            rest = stripped[len("CHECK QUESTION:"):].strip()
            if rest:
                lines.append(rest)
        elif current is not None:
            lines.append(line)

    if current:
        result[current] = "\n".join(lines).strip()

    if not result["explanation"]:
        result["explanation"] = raw.strip()
        result["check_question"] = "Can you summarize what you just learned in one sentence?"

    return result


async def assess_answer(check_question: str, user_answer: str, topic: str) -> dict:
    """Ask the LLM to assess whether the student understood."""
    prompt = f"""You are a Python tutor assessing a student's answer.

Topic: {topic}
Question asked: {check_question}
Student's answer: {user_answer}

Reply in this EXACT format:

UNDERSTOOD: yes or no
FEEDBACK:
<one or two sentences of encouraging feedback>"""

    raw = await ask_llm(prompt)
    understood = False
    feedback_lines: list[str] = []
    capturing_feedback = False

    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("UNDERSTOOD:"):
            understood = "yes" in stripped.lower()
        elif stripped.startswith("FEEDBACK:"):
            capturing_feedback = True
            rest = stripped[len("FEEDBACK:"):].strip()
            if rest:
                feedback_lines.append(rest)
        elif capturing_feedback and stripped:
            feedback_lines.append(stripped)

    return {
        "understood": understood,
        "feedback": " ".join(feedback_lines).strip() or "Good effort!",
    }
