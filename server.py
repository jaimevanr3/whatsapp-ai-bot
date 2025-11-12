from flask import Flask, request
import os, requests

app = Flask(__name__)

TWILIO_SID    = os.getenv("TWILIO_SID")
TWILIO_AUTH   = os.getenv("TWILIO_AUTH")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")  # e.g. 'whatsapp:+1415XXXXXXX'

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    sender   = request.form.get("From")        # 'whatsapp:+27...'
    incoming = (request.form.get("Body") or "").strip()
    reply    = f"Echo: {incoming}" if incoming else "Hello!"
    url      = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data     = {"From": TWILIO_NUMBER, "To": sender, "Body": reply}
    requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_AUTH))
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
