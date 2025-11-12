from flask import Flask, request
import os, requests, json, sys

app = Flask(__name__)

TWILIO_SID    = os.getenv("TWILIO_SID")
TWILIO_AUTH   = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
OPENAI_KEY    = os.getenv("OPENAI_API_KEY")

AIRTABLE_PAT   = os.getenv("AIRTABLE_PAT")
AIRTABLE_BASE  = os.getenv("AIRTABLE_BASE")
AIRTABLE_TABLE = os.getenv("AIRTABLE_TABLE")

def ai_reply(user_text):
    try:
        body = {"model":"gpt-4o-mini",
                "messages":[
                    {"role":"system","content":"You are a helpful WhatsApp assistant."},
                    {"role":"user","content":user_text or "Hello"}]}
        r = requests.post("https://api.openai.com/v1/chat/completions",
                          headers={"Authorization":f"Bearer {OPENAI_KEY}",
                                   "Content-Type":"application/json"},
                          data=json.dumps(body))
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("[DEBUG] OpenAI error:", e, file=sys.stdout, flush=True)
        return f"Echo: {user_text}"

def save_to_airtable(phone, incoming, reply):
    if not (AIRTABLE_PAT and AIRTABLE_BASE and AIRTABLE_TABLE):
        print("[DEBUG] Missing Airtable env vars", file=sys.stdout, flush=True)
        return
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE}/{AIRTABLE_TABLE}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_PAT}",
        "Content-Type": "application/json"
    }
    data = {
        "records": [{
            "fields": {
                "Phone": phone,
                "LastMessage": incoming,
                "AIReply": reply,
                "Status": "New"
            }
        }]
    }
    try:
        r = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
        print("[DEBUG] Airtable status:", r.status_code, file=sys.stdout, flush=True)
        print("[DEBUG] Airtable response:", r.text[:300], file=sys.stdout, flush=True)
    except Exception as e:
        print("[DEBUG] Airtable exception:", e, file=sys.stdout, flush=True)

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    sender   = request.form.get("From")
    incoming = (request.form.get("Body") or "").strip()
    reply = ai_reply(incoming)
    # send via Twilio
    twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = {"From": TWILIO_NUMBER, "To": sender, "Body": reply}
    requests.post(twilio_url, data=data, auth=(TWILIO_SID, TWILIO_AUTH))
    # log to Airtable
    save_to_airtable(sender, incoming, reply)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
