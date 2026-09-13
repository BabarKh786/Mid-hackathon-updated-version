import json
from groq import Groq
from config import GROQ_MODEL, groq_api_key

def client():
    key = groq_api_key()
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to Streamlit Cloud Secrets "
            "or your local .streamlit/secrets.toml."
        )
    return Groq(api_key=key)

def ask_json(system_prompt, user_prompt):
    c = client()
    resp = c.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
        reasoning_effort="medium",
    )
    text = resp.choices[0].message.content
    try:
        return json.loads(text)
    except Exception as exc:
        raise RuntimeError(f"GPT-OSS returned invalid JSON: {exc}") from exc
