import os
from datetime import datetime, timedelta

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "UniMind backend is running"}), 200
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Firebase Admin
import firebase_admin
from firebase_admin import credentials, firestore

# ----------------------------------------------------
# ENV + APP
# ----------------------------------------------------
load_dotenv()

app = Flask(__name__)

# allow your React app
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5001")
CORS(
    app,
    resources={r"/api/*": {"origins": FRONTEND_ORIGIN}},
    supports_credentials=True,
)


@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
    response.headers.add("Access-Control-Allow-Origin", FRONTEND_ORIGIN)
    return response


# ----------------------------------------------------
# ENV VARS
# ----------------------------------------------------
BLOSSOMS_API_KEY = os.getenv("BLOSSOMS_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

# ----------------------------------------------------
# FIREBASE INIT (only once)
# ----------------------------------------------------
firebase_db = None
try:
    if FIREBASE_CREDENTIALS and os.path.exists(FIREBASE_CREDENTIALS):
        # avoid double init
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS)
            firebase_admin.initialize_app(cred)
        firebase_db = firestore.client()
        print("✅ Firebase initialized")
    else:
        print("⚠️ Firebase credentials not found/missing")
except Exception as e:
    print("❌ Firebase init error:", e)

# ----------------------------------------------------
# IN-MEMORY FALLBACKS
# ----------------------------------------------------
chat_sessions = {}
journal_entries = {}
user_profiles = {}  # for UniBoard/xp


def add_xp_and_move(user_id: str, xp_amount: int = 10):
    """UniBoard-style simple progress."""
    profile = user_profiles.get(user_id, {"xp": 0, "board_pos": 0})
    profile["xp"] += int(xp_amount)
    profile["board_pos"] = (profile["board_pos"] + 1) % 20
    user_profiles[user_id] = profile
    return profile


# ----------------------------------------------------
# HEALTH
# ----------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "UniMind API is running"}), 200


# ----------------------------------------------------
# EMOTION (Blossoms)
# ----------------------------------------------------
def detect_emotion(message: str):
    if not BLOSSOMS_API_KEY:
      # fallback
        return {
            "emotion": "neutral",
            "intensity": 0.5,
            "confidence": 0.7,
            "note": "Using mock data - add BLOSSOMS_API_KEY to environment",
        }

    try:
        resp = requests.post(
            "https://api.blossoms.ai/v1/analyze",
            headers={
                "Authorization": f"Bearer {BLOSSOMS_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"text": message},
            timeout=10,
        )
        return resp.json() if resp.status_code == 200 else {"emotion": "neutral"}
    except Exception as e:
        return {"emotion": "neutral", "note": f"Error: {e}"}


# ----------------------------------------------------
# CHAT (use the nicer version from your 2nd file)
# ----------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")
        user_id = data.get("user_id", "demo_user")
        calendar_events = data.get("calendar_events", [])

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # pull last messages from Firestore (best effort)
        recent_history = []
        if firebase_db:
            try:
                chats_ref = (
                    firebase_db.collection("users")
                    .document(user_id)
                    .collection("chats")
                )
                docs = list(chats_ref.stream())
                for doc in docs[-8:]:
                    msg = doc.to_dict()
                    if msg.get("user_message"):
                        recent_history.append(
                            {"role": "user", "content": msg["user_message"]}
                        )
                    if msg.get("ai_response"):
                        recent_history.append(
                            {"role": "assistant", "content": msg["ai_response"]}
                        )
            except Exception as e:
                print("⚠️ Firestore read error:", e)

        # add current user message
        recent_history.append({"role": "user", "content": user_message})

        # emotion & calendar context
        emotion_data = detect_emotion(user_message)
        emotion = emotion_data.get("emotion", "neutral")
        intensity = emotion_data.get("intensity", 0.5)

        calendar_context = ""
        if calendar_events:
            event_list = "\n".join(
                [f"- {e['title']} on {e['date']}" for e in calendar_events[:3]]
            )
            calendar_context = f"\n\nUpcoming events:\n{event_list}"

        system_prompt = f"""You are UniMind, a compassionate AI wellness companion for college students.
Current emotional tone: {emotion} (intensity: {intensity}/1.0).{calendar_context}
Be warm, empathetic, concise (2–3 sentences)."""

        ai_response = "I'm here for you."
        if OPENROUTER_API_KEY:
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [{"role": "system", "content": system_prompt}]
                    + recent_history,
                    "max_tokens": 200,
                },
                timeout=25,
            )
            if r.status_code == 200:
                data = r.json()
                ai_response = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", ai_response)
                )

        # save chat
        chat_entry = {
            "user_message": user_message,
            "ai_response": ai_response,
            "emotion": emotion_data,
            "timestamp": datetime.now().isoformat(),
        }

        if firebase_db:
            firebase_db.collection("users").document(user_id).collection(
                "chats"
            ).add(chat_entry)

        # also give xp
        add_xp_and_move(user_id, xp_amount=15)

        return (
            jsonify(
                {
                    "response": ai_response,
                    "emotion": emotion_data,
                    "timestamp": chat_entry["timestamp"],
                }
            ),
            200,
        )

    except Exception as e:
        print("❌ Chat error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat/history", methods=["GET"])
def get_chat_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    if not firebase_db:
        return jsonify({"messages": []}), 200

    try:
        chats_ref = (
            firebase_db.collection("users").document(user_id).collection("chats")
        )
        docs = chats_ref.order_by("timestamp").stream()
        history = [doc.to_dict() for doc in docs]
        return jsonify({"messages": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------
# JOURNAL (use per-user Firestore version)
# ----------------------------------------------------
@app.route("/api/journal", methods=["POST"])
def add_journal_entry():
    try:
        data = request.json
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        entry = {
            "mood": data.get("mood"),
            "mood_text": data.get("mood_text", ""),
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "timestamp": datetime.now().isoformat(),
        }

        if firebase_db:
            doc_ref = (
                firebase_db.collection("users")
                .document(user_id)
                .collection("journals")
                .add(entry)
            )
            entry_id = doc_ref[1].id
        else:
            # in-memory fallback
            journal_entries.setdefault(user_id, []).append(entry)
            entry_id = "local"

        add_xp_and_move(user_id, xp_amount=10)

        return jsonify({"message": "Journal entry saved", "id": entry_id, "entry": entry}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/journal", methods=["GET"])
def get_journals():
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        if not firebase_db:
            entries = journal_entries.get(user_id, [])
            entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
            return jsonify({"entries": entries, "count": len(entries)}), 200

        journals_ref = (
            firebase_db.collection("users").document(user_id).collection("journals")
        )
        docs = journals_ref.stream()
        entries = []
        for d in docs:
            e = d.to_dict()
            e["id"] = d.id
            entries.append(e)

        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return jsonify({"entries": entries, "count": len(entries)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/journal/<entry_id>", methods=["DELETE"])
def delete_journal_entry(entry_id):
    try:
        user_id = request.args.get("user_id")
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        if not firebase_db:
            return jsonify({"error": "Firestore not configured"}), 500

        entry_ref = (
            firebase_db.collection("users")
            .document(user_id)
            .collection("journals")
            .document(entry_id)
        )
        if not entry_ref.get().exists:
            return jsonify({"error": "Entry not found"}), 404

        entry_ref.delete()
        return jsonify({"success": True, "deleted_id": entry_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------
# RESOURCES (take the v1/nearby version from your 1st file)
# ----------------------------------------------------
GLOBAL_RESOURCES = [
    {
        "name": "988 Suicide & Crisis Lifeline",
        "description": "24/7 free & confidential",
        "url": "https://988lifeline.org",
    },
    {
        "name": "Crisis Text Line",
        "description": "Text HOME to 741741 (US/CA)",
        "url": "https://www.crisistextline.org",
    },
    {
        "name": "7 Cups",
        "description": "Free emotional support & affordable therapy",
        "url": "https://www.7cups.com",
    },
    {
        "name": "SAMHSA National Helpline",
        "description": "Treatment referral & info",
        "url": "https://findtreatment.gov",
    },
]


@app.route("/api/resources", methods=["GET"])
def get_resources():
    try:
        school = request.args.get("school", "").strip()
        if not school:
            return jsonify({"error": "Missing school parameter"}), 400

        GOOGLE_KEY = GOOGLE_PLACES_API_KEY
        if not GOOGLE_KEY:
            # just return globals
            return jsonify(
                {"global": GLOBAL_RESOURCES, "school_specific": []}
            ), 200

        # 1) geocode school
        geo = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": f"{school} university campus", "key": GOOGLE_KEY},
            timeout=10,
        ).json()

        if not geo.get("results"):
            return (
                jsonify(
                    {
                        "global": GLOBAL_RESOURCES,
                        "school_specific": [
                            {
                                "name": school,
                                "description": "Not found. Try full college name.",
                            }
                        ],
                    }
                ),
                200,
            )

        loc = geo["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]

        # 2) Places API v1 nearby
        places_url_nearby = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_KEY,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.googleMapsUri",
        }
        nearby_payload = {
            "includedTypes": [
                "doctor",
                "psychologist",
                "psychiatrist",
                "hospital",
                "clinic",
                "university",
                "school",
            ],
            "maxResultCount": 20,
            "rankPreference": "DISTANCE",
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": 32187,
                }
            },
        }
        nearby_resp = requests.post(
            places_url_nearby,
            headers=headers,
            json=nearby_payload,
            timeout=12,
        )
        nearby_json = nearby_resp.json()

        def normalize(places_list):
            out = []
            for p in places_list:
                name = (p.get("displayName") or {}).get("text")
                addr = p.get("formattedAddress") or "Address not available"
                maps = p.get("googleMapsUri") or "#"
                if name:
                    out.append(
                        {"name": name, "description": addr, "url": maps}
                    )
            return out

        local = normalize(nearby_json.get("places", []))

        # fallback to text search if empty
        if not local:
            places_url_text = "https://places.googleapis.com/v1/places:searchText"
            text_payload = {
                "textQuery": "mental health OR counseling OR wellness center OR therapy",
                "maxResultCount": 20,
                "locationBias": {
                    "circle": {
                        "center": {"latitude": lat, "longitude": lng},
                        "radius": 32187,
                    }
                },
            }
            text_resp = requests.post(
                places_url_text,
                headers=headers,
                json=text_payload,
                timeout=12,
            )
            text_json = text_resp.json()
            local = normalize(text_json.get("places", []))

        return (
            jsonify(
                {
                    "global": GLOBAL_RESOURCES,
                    "school_specific": local
                    or [
                        {
                            "name": school,
                            "description": "No nearby resources found.",
                        }
                    ],
                }
            ),
            200,
        )
    except Exception as e:
        print("resource error:", e)
        return (
            jsonify(
                {
                    "global": GLOBAL_RESOURCES,
                    "school_specific": [
                        {"name": "Server Error", "description": str(e)}
                    ],
                }
            ),
            500,
        )


# ----------------------------------------------------
# CALENDAR MOCK
# ----------------------------------------------------
@app.route("/api/calendar/events", methods=["GET"])
def get_calendar_events():
    mock_events = [
        {"title": "History Exam", "date": "April 25", "time": "10:00 AM"},
        {"title": "Presentation Discussion", "date": "April 20", "time": "1:00 PM"},
        {"title": "Physics Exam", "date": "April 21", "time": "10:00 AM"},
    ]
    return jsonify({"events": mock_events}), 200


# ----------------------------------------------------
# FIREBASE TEST
# ----------------------------------------------------
@app.route("/api/firebase-test", methods=["GET"])
def firebase_test():
    try:
        if not firebase_db:
            return jsonify({"status": "error", "message": "Firebase not initialized"}), 500

        test_data = {
            "message": "Hello from Flask!",
            "timestamp": datetime.now().isoformat(),
        }
        firebase_db.collection("test_connection").add(test_data)
        return jsonify({"status": "success", "message": "Data written to Firestore"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ----------------------------------------------------
# UNIBOARD / XP (from your first file)
# ----------------------------------------------------
@app.route("/api/xp", methods=["POST"])
def add_xp():
    try:
        body = request.get_json(force=True)
        user_id = body.get("user_id", "demo_user")
        amount = int(body.get("amount", 10))
        prof = user_profiles.get(user_id, {"xp": 0, "board_pos": 0})
        prof["xp"] += amount
        user_profiles[user_id] = prof
        return jsonify({"xp": prof["xp"]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/uniboard", methods=["GET"])
def get_uniboard():
    user_id = request.args.get("user_id", "demo_user")
    profile = user_profiles.get(user_id, {"xp": 0, "board_pos": 0})
    xp_total = profile["xp"]
    xp_goal = 600
    board_pos = profile["board_pos"]
    badges = xp_total // 100

    progress = {
        "academics": min(5, xp_total // 120),
        "mental_health": min(5, xp_total // 100),
        "life_balance": min(5, xp_total // 140),
        "connection": min(5, xp_total // 150),
        "creativity": min(5, xp_total // 160),
    }

    move_message = f"You’re on tile {board_pos}. Keep it up! 🌱"

    return jsonify(
        {
            "move_message": move_message,
            "progress": progress,
            "xp": {"total": xp_total, "goal": xp_goal},
            "badges": badges,
            "board_pos": board_pos,
        }
    )


# ----------------------------------------------------
# RUN
# ----------------------------------------------------
if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=8000, debug=debug_mode)
