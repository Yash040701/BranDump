import os
import sqlite3
import requests
from flask import Flask, request, Response, jsonify
from twilio.twiml.voice_response import VoiceResponse, Connect
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a silent thought collector called "Dump".
Your only job is to help the caller empty their mind.

Rules:
- Greet them with exactly: "Hey, go ahead — what's on your mind?"
- Listen without interrupting
- After they pause, say things like "Got it, keep going" or "Mm-hmm, what else?"
- NEVER give advice, opinions, or feedback on their content
- NEVER ask questions about what they said
- After a long silence (5+ seconds), ask: "Anything else on your mind?"
- If they say they're done, say: "Got it, I'll send you a summary shortly. Bye!"
- Keep all responses under 8 words
"""

# ─── Database Setup ───────────────────────────────────────────────────────────
DB_PATH = "braindump.db"

def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dumps (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id     TEXT UNIQUE NOT NULL,
            transcript  TEXT,
            summary     TEXT,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print("✅ Database ready")

def save_dump(call_id, transcript, summary):
    """Save a transcript to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO dumps (call_id, transcript, summary) VALUES (?, ?, ?)",
        (call_id, transcript, summary)
    )
    conn.commit()
    conn.close()
    print(f"💾 Saved transcript for callId: {call_id}")

# ─── POST /incoming-call ──────────────────────────────────────────────────────
@app.route("/incoming-call", methods=["POST"])
def incoming_call():
    print("\n📞 Incoming call received")

    base_url = os.getenv("PUBLIC_URL")  # e.g. https://abc123.ngrok-free.app

    try:
        response = requests.post(
            "https://api.ultravox.ai/api/calls",
            headers={
                "X-API-Key": os.getenv("ULTRAVOX_API_KEY"),
                "Content-Type": "application/json",
            },
            json={
                "systemPrompt": SYSTEM_PROMPT,
                "voice": "Mark",
                "temperature": 0.4,
                "firstSpeaker": "FIRST_SPEAKER_AGENT",
                "medium": {"twilio": {}},
                "callbacks": {
                    "ended": {
                        "url": f"{base_url}/call-ended"   # ← Ultravox hits this when call ends
                    }
                }
            },
        )

        response.raise_for_status()
        data = response.json()

        join_url = data["joinUrl"]
        call_id  = data["callId"]

        print(f"✅ Ultravox session created | callId: {call_id}")
        print(f"🔗 joinUrl: {join_url}")

        twiml = VoiceResponse()
        connect = Connect()
        connect.stream(url=join_url)
        twiml.append(connect)

        return Response(str(twiml), mimetype="text/xml")

    except requests.exceptions.RequestException as e:
        print(f"❌ Ultravox API error: {e}")
        print(f"❌ Response: {e.response.text if e.response else 'No response'}")
        twiml = VoiceResponse()
        twiml.say("Sorry, something went wrong. Please try again.")
        return Response(str(twiml), mimetype="text/xml")


# ─── POST /call-ended ─────────────────────────────────────────────────────────
# Ultravox hits this automatically when the call ends
@app.route("/call-ended", methods=["POST"])
def call_ended():
    print("\n📵 Call ended webhook received")

    data = request.json
    print(f"📦 Payload keys: {list(data.keys())}")

    # Extract call data from the webhook payload
    call_data = data.get("call", {})
    call_id = call_data.get("callId")

    if not call_id:
        print("❌ No callId in webhook payload")
        return jsonify({"error": "No callId"}), 400

    # Get data directly from webhook payload
    summary = call_data.get("summary")
    transcript = call_data.get("transcript")  # May not be present in webhook
    if summary:
        short_summary = summary[:120] + "..." if len(summary) > 120 else summary

        sms_body = f"🧠 {short_summary}"
        
        try:
            twilio_client.messages.create(
                body=sms_body,
                from_=os.getenv("TWILIO_PHONE_NUMBER"),
                to=os.getenv("YOUR_PHONE_NUMBER")
            )
            print(f"📱 SMS sent to {os.getenv('YOUR_PHONE_NUMBER')}")

        except Exception as e:
            print(f"❌ Failed to send SMS: {e}")


    print(f"📝 Summary: {summary}")
    if transcript:
        print(f"📝 Transcript length: {len(transcript)} characters")
    else:
        print("📝 Transcript: Not available in webhook payload")

    # Save to SQLite
    save_dump(call_id, transcript, summary)

    return jsonify({"status": "ok"}), 200


# ─── GET /dumps ───────────────────────────────────────────────────────────────
# View all your saved brain dumps
@app.route("/dumps", methods=["GET"])
def get_dumps():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dumps ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    dumps = [dict(row) for row in rows]
    return jsonify(dumps)


# ─── GET /health ──────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Brain Dump server is running 🧠"})


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 3000))
    print(f"\n🚀 Brain Dump server running on port {port}")
    print(f"📡 Health check  : http://localhost:{port}/health")
    print(f"📞 Incoming call : http://localhost:{port}/incoming-call")
    print(f"📵 Call ended    : http://localhost:{port}/call-ended")
    print(f"📋 View dumps    : http://localhost:{port}/dumps\n")
    app.run(port=port, debug=True)