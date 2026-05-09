# 🧠 BrainDump AI

> Call a number. Talk freely. Get a summary SMS.

BrainDump is a voice-powered thought collector built with **Ultravox** and **Twilio**.  
Call your number, dump everything on your mind, hang up — and within seconds a clean summary lands on your phone.

---

## How It Works

```
📞 You call your Twilio number
        ↓
🎙️  Ultravox answers and listens silently
        ↓
📵  You hang up
        ↓
📝  Ultravox generates a summary
        ↓
📱  Twilio SMS sends it to your phone
        ↓
💾  Everything saved to SQLite
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Phone number | Twilio |
| Voice AI | Ultravox |
| Backend | Python + Flask |
| Database | SQLite |
| Tunnel (dev) | ngrok |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/braindump-ai.git
cd braindump-ai
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Fill in your `.env`:

```bash
ULTRAVOX_API_KEY=your_ultravox_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
YOUR_PHONE_NUMBER=+91xxxxxxxxxx
PUBLIC_URL=https://abc123.ngrok-free.app
```

### 5. Run the server

```bash
python server.py
```

### 6. Expose with ngrok

```bash
ngrok http 3000
```

Copy the `https://` URL and update `PUBLIC_URL` in your `.env`.

### 7. Connect Twilio

1. Twilio Console → Phone Numbers → Your number
2. Voice Configuration → "A Call Comes In" → Webhook
3. URL: `https://your-ngrok-url.ngrok-free.app/incoming-call`
4. Method: HTTP POST → Save

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/incoming-call` | POST | Twilio webhook — starts Ultravox session |
| `/call-ended` | POST | Ultravox webhook — saves summary, sends SMS |
| `/dumps` | GET | View all saved brain dumps |
| `/health` | GET | Health check |

---

## Environment Variables

| Variable | Description |
|---|---|
| `ULTRAVOX_API_KEY` | From app.ultravox.ai |
| `TWILIO_ACCOUNT_SID` | From Twilio Console |
| `TWILIO_AUTH_TOKEN` | From Twilio Console |
| `TWILIO_PHONE_NUMBER` | Your Twilio number (with +) |
| `YOUR_PHONE_NUMBER` | Your personal number (with +) |
| `PUBLIC_URL` | Your ngrok URL (no trailing slash) |

---

## Phases Built

- ✅ **Phase 1** — Twilio + Ultravox voice call integration
- ✅ **Phase 2** — Transcript + summary saved to SQLite
- ✅ **Phase 3** — Auto SMS summary after every call

---

## Notes

- Uses Ultravox free tier — limited minutes per month
- Uses Twilio trial — SMS prepends "Sent from a Twilio trial account"
- Database (`braindump.db`) is local and gitignored — your thoughts stay private
