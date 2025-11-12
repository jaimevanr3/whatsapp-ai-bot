from flask import Flask, request
import os, requests, json, sys

app = Flask(__name__)

# Twilio
TWILIO_SID    = os.getenv("TWILIO_SID")
TWILIO_AUTH   = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")

# OpenAI
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

def ai_reply(user_text: str) -> str:
    # Debug: log whether key is present
    print(f"[DEBUG] OPENAI_KEY present? {bool(OPENAI_KEY)}", file=sys.stdout, flush=True)

    if not OPENAI_KEY:
        return f"Echo: {user_text}" if user_text else "Hello!"

    try:
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role":"system","content":
                 "You are a WhatsApp assistant. Reply in 1–3 short, friendly sentences. "
                 "If unclear, ask exactly one clarifying question."},
                {"role":"user","content": user_text or "Hello"}
            ]
        }
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_KEY}",
                "Content-Type": "application/json"
            },
            data=json.dumps(body),
            timeout=30
        )
        # Debug: log status / errors
        print(f"[DEBUG] OpenAI status: {r.status_code}", file=sys.stdout, flush=True)
        if r.status_code != 200:
            print(f"[DEBUG] OpenAI error body: {r.text[:400]}", file=sys.stdout, flush=True)
            return f"Echo: {user_text}" if user_text else "Hello!"
        out = r.json()["choices"][0]["message"]["content"].strip()
        return "🤖 " + out
    except Exception as e:
        print(f"[DEBUG] OpenAI exception: {e}", file=sys.stdout, flush=True)
        return f"Echo: {user_text}" if user_text else "Hello!"

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    sender   = request.form.get("From")
    incoming = (request.form.get("Body") or "").strip()

    reply = ai_reply(incoming)

    # Send via Twilio
    url  = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = {"From": TWILIO_NUMBER, "To": sender, "Body": reply}
    requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_AUTH), timeout=20)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
