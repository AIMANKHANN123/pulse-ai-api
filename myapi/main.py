import json
import os
import random
import re
from datetime import datetime

import requests
from fastapi import Body, FastAPI

app = FastAPI(title="Pulse AI Question Generator")

# -----------------------
# 🔑 API Config
# -----------------------
PULSE_BEARER_TOKEN = "3673|1Cg9jkntwA0827JLsmIoUoR4E2hOj2sLkMwEYF8dcdd9ed59"
COMPANY_ID = "4"
BASE_URL = "https://pulse-survey.ospreyibs.com/api/v1"

headers = {
    "Authorization": f"Bearer {PULSE_BEARER_TOKEN}",
    "Company-Id": COMPANY_ID,
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# -----------------------
# 🧠 Detect Question Type
# -----------------------
def detect_question_type(question: str) -> str:
    q = question.lower()
    if re.search(r"(on a scale of|how likely|1-10|1 to 10|rate.*10|0-10|0 to 10)", q):
        return "nps-style"
    if re.search(r"(how satisfied|rate|scale\s*1-5|1 to 5)", q):
        return "scale"
    if re.search(r"(do you|have you|is your|are you|would you|did you|can you)", q):
        return "binary"
    if re.search(r"(why|what|how can|describe|explain|suggest|improve)", q):
        return "open-ended"
    return "open-ended"

# -----------------------
# 💡 Generate Questions from Prompt
# -----------------------
def generate_questions_from_prompt(prompt: str, num: int = 5):
    base_topic = re.sub(r"generate.*?about", "", prompt, flags=re.IGNORECASE).strip()
    base_topic = base_topic if base_topic else "workplace"
    templates = [
        f"How satisfied are you with {base_topic}?",
        f"Do you feel confident about {base_topic} in your team?",
        f"What can improve {base_topic} in your organization?",
        f"On a scale of 1-5, how would you rate {base_topic}?",
        f"How likely are you to recommend our {base_topic} practices to others?"
    ]
    random.shuffle(templates)
    selected = templates[:num]
    return [{"question": q, "type": detect_question_type(q)} for q in selected]

# -----------------------
# 💾 Save Chat History
# -----------------------
def save_to_history(prompt, results):
    history_file = "chat_history.json"
    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            data = json.load(f)
    else:
        data = []

    chat_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": prompt,
        "response": results
    }

    data.append(chat_entry)
    with open(history_file, "w") as f:
        json.dump(data, f, indent=4)

# -----------------------
# 🌐 Root Route
# -----------------------
@app.get("/")
def home():
    return {"message": "Pulse AI Question Generator API 🚀"}

# -----------------------
# 💬 POST /generate (Chatbot-like)
# -----------------------
@app.post("/generate")
def generate_from_prompt(data: dict = Body(...)):
    prompt = data.get("prompt", "")
    if not prompt:
        return {"error": "Please provide a prompt text."}

    generated = generate_questions_from_prompt(prompt)
    random.shuffle(generated)

    # 💾 Save chat to history
    save_to_history(prompt, generated)

    return {"prompt": prompt, "generated_count": len(generated), "results": generated}

# -----------------------
# 📜 GET /history (View Chat History)
# -----------------------
@app.get("/history")
def get_chat_history():
    history_file = "chat_history.json"
    if not os.path.exists(history_file):
        return {"message": "No history found yet."}
    with open(history_file, "r") as f:
        data = json.load(f)
    return {"total_chats": len(data), "chats": data}
