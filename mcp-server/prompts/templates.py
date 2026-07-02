"""
prompts/templates.py — Per-tool prompt builders.

WHY THIS FILE EXISTS:
  Each MCP tool makes its own focused Claude API call with a purpose-built prompt.
  These templates are the instructions for those inner calls.

  Keeping them here (not inside tool files) means:
    - You can read all prompt logic in one place.
    - Prompt changes don't require touching tool business logic.
    - You can A/B test prompts by swapping templates without changing tool signatures.

PROMPT DESIGN PRINCIPLES USED HERE:
  1. Specify the output format exactly — Claude should return pure JSON matching
     the schema. State the JSON structure explicitly.
  2. Give examples of good vs bad output. Claude is a better prompt-follower
     when it sees what you want, not just a description of it.
  3. Keep each prompt focused on one task. Don't combine explanation + checking
     into a single prompt — do them as separate focused calls.
  4. Put the most important constraint LAST in the prompt — recency matters.
"""

from __future__ import annotations


def explain_concept_prompt(question: str, code: str | None) -> str:
    """
    Prompt for the explain_concept tool's internal Claude call.

    Instructs Claude to generate a structured explanation and return JSON
    matching ExplainConceptOutput schema.
    """
    code_section = ""
    if code:
        code_section = f"""
The user also provided this code snippet:
```python
{code}
```
Reference specific lines from this code in your explanation.
"""

    return f"""\
You are generating a structured Python explanation for a beginner-to-intermediate learner.

User question: {question}
{code_section}

Generate a clear, beginner-friendly explanation and return it as JSON.

RULES FOR THE EXPLANATION:
- Use plain English. Avoid jargon unless you immediately define it.
- Include a short code example (10–20 lines) that demonstrates the concept.
- Find a real-world analogy if it genuinely helps (skip it if it feels forced).
- Identify the canonical topic name (e.g. "decorators", "list comprehensions").
- Extract 2–4 core concepts the learner must grasp.

RETURN THIS EXACT JSON STRUCTURE (no markdown, no extra text — pure JSON only):
{{
  "explanation": "string — the full explanation, 100–300 words",
  "topic": "string — canonical topic name, lowercase, e.g. 'decorators'",
  "key_concepts": ["concept 1", "concept 2", "concept 3"],
  "code_example": "string — illustrative code or null if user's code is sufficient",
  "analogy": "string — real-world analogy or null"
}}

Return pure JSON only. No markdown fences. No explanation before or after the JSON.\
"""


def generate_check_prompt(
    explanation: str,
    topic: str,
    key_concepts: list[str],
) -> str:
    """
    Prompt for the generate_comprehension_check tool's internal Claude call.

    The check question must test genuine understanding, not recitation.
    The signals define what "correct" and "incorrect" look like.
    """
    concepts_str = "\n".join(f"  - {c}" for c in key_concepts)

    return f"""\
You are generating a comprehension check question for a Python learner.

Topic: {topic}
Key concepts that were explained:
{concepts_str}

Explanation given to the learner:
---
{explanation}
---

Generate exactly ONE comprehension check question and return it as JSON.

RULES FOR THE QUESTION:
- Must test genuine understanding, not memory or recitation.
  BAD:  "What does a decorator do?" (answered by repeating the explanation)
  GOOD: "If you remove the @my_decorator line, what changes about how the function runs?"
- Must have a specific, demonstrable correct answer.
- Must probe one of the key concepts listed above.
- Should be answerable in 2–4 sentences by someone who truly understood.

RULES FOR CORRECT SIGNALS:
- 3–5 phrases/ideas that appear in a correct answer.
- These are patterns, not an exact answer. Different wordings can be correct.
- Example for decorators: ["wraps the original function", "called at definition time",
  "returns a callable", "adds behaviour without modifying the original"]

RULES FOR MISCONCEPTION SIGNALS:
- 2–3 phrases that reveal a specific common misunderstanding.
- Example for decorators: ["modifies the function in place", "only works on methods",
  "changes the function's name permanently"]

RETURN THIS EXACT JSON STRUCTURE (pure JSON only, no markdown):
{{
  "question": "string — the single check question",
  "correct_signals": ["signal 1", "signal 2", "signal 3"],
  "misconception_signals": ["misconception 1", "misconception 2"],
  "hint": "string — a gentle hint that points toward the concept without giving it away"
}}

Return pure JSON only. No markdown fences. No text before or after.\
"""


def assess_answer_prompt(
    check_question: str,
    user_answer: str,
    explanation: str,
    correct_signals: list[str],
    misconception_signals: list[str],
    topic: str,
) -> str:
    """
    Prompt for the assess_answer tool's internal Claude call.

    The assessor has full context: the question, the user's answer,
    the original explanation, and the signal lists. Rich context = accurate assessment.
    """
    correct_str = "\n".join(f"  - {s}" for s in correct_signals)
    misconception_str = "\n".join(f"  - {s}" for s in misconception_signals)

    return f"""\
You are assessing whether a Python learner genuinely understood a concept.

Topic: {topic}

Original explanation given to the learner:
---
{explanation}
---

Check question that was asked:
{check_question}

User's answer:
{user_answer}

Signals indicating a CORRECT understanding (answer should contain these ideas):
{correct_str}

Signals indicating a MISCONCEPTION (answer may contain these):
{misconception_str}

Assess the user's understanding and return JSON.

ASSESSMENT RULES:
- understood=true if the answer covers at least 2 correct signals without triggering misconception signals.
- understood=false if the answer triggers a misconception signal OR misses all correct signals.
- Be generous with partial credit: if the learner has the right idea but expresses it imperfectly,
  that is understood=true with a score of 70–85 and encouraging feedback.
- score 90–100: demonstrates clear, confident understanding
- score 70–89: correct but could be more precise
- score 40–69: partial understanding, key gap exists
- score 0–39: significant misconception or no understanding shown

FEEDBACK RULES:
- Write in coaching language. Never say "wrong", "incorrect", "score", "grade", "fail".
- If correct: affirm specifically what they got right.
  Good: "Exactly — you identified that the decorator is called at definition time, not call time."
- If incorrect: name the gap without discouraging.
  Good: "You're close — the tricky part here is WHEN the decorator runs. Let me show you..."
- re_explain_angle: suggest ONE specific angle for re-explanation if understood=false.
  Options: "real-world analogy", "step-by-step code trace", "contrast with broken version",
  "simplest possible working example"

RETURN THIS EXACT JSON STRUCTURE (pure JSON only, no markdown):
{{
  "understood": true or false,
  "score": 0–100,
  "feedback": "string — specific, coaching-language feedback (2–3 sentences)",
  "misconception": "string describing the misconception or null",
  "re_explain_angle": "string — angle for re-explanation or null if understood=true"
}}

Return pure JSON only. No markdown fences. No text before or after.\
"""
