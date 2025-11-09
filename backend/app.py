import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
from firebase_admin import firestore


# Load environment variables from .env
load_dotenv()

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)
from flask_cors import CORS

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5001")

CORS(app, resources={r"/api/*": {"origins": FRONTEND_ORIGIN}}, supports_credentials=True)

@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
    response.headers.add("Access-Control-Allow-Origin", FRONTEND_ORIGIN)
    return response


# Environment variables
BLOSSOMS_API_KEY = os.getenv('BLOSSOMS_API_KEY')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')

# Initialize Firebase
firebase_db = None
try:
    if FIREBASE_CREDENTIALS and os.path.exists(FIREBASE_CREDENTIALS):
        cred = credentials.Certificate(FIREBASE_CREDENTIALS)
        firebase_admin.initialize_app(cred)
        firebase_db = firestore.client()
        print("✅ Firebase initialized successfully")
    else:
        print("⚠️ Firebase credentials not found or path missing")
except Exception as e:
    print(f"❌ Firebase initialization error: {e}")

# In-memory fallback data
chat_sessions = {}
journal_entries = {}
user_profiles = {}

# -----------------------------------------------------------
# Health Check
# -----------------------------------------------------------
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "UniMind API is running"}), 200

# -----------------------------------------------------------
# Chat Endpoint
# -----------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        print("📩 Chat request received")  # ✅ Debug 1

        data = request.json
        user_message = data.get("message", "")
        user_id = data.get("user_id", "demo_user")
        calendar_events = data.get("calendar_events", [])

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        # 🧠 Fetch recent history
        print("🔍 Loading recent messages for", user_id)  # ✅ Debug 2
        recent_history = []
        try:
            if firebase_db:
                chats_ref = firebase_db.collection("users").document(user_id).collection("chats")
                # Try a safer fetch first
                docs = list(chats_ref.stream())
                for doc in docs[-8:]:  # manually limit to last 8
                    msg = doc.to_dict()
                    if msg.get("user_message"):
                        recent_history.append({"role": "user", "content": msg["user_message"]})
                    if msg.get("ai_response"):
                        recent_history.append({"role": "assistant", "content": msg["ai_response"]})
        except Exception as e:
            print("⚠️ Firestore memory error:", e)
            recent_history = []

        # Add the current user message
        recent_history.append({"role": "user", "content": user_message})

        # Emotion context
        emotion_data = detect_emotion(user_message)
        emotion = emotion_data.get("emotion", "neutral")
        intensity = emotion_data.get("intensity", 0.5)

        calendar_context = ""
        if calendar_events:
            event_list = "\n".join([f"- {e['title']} on {e['date']}" for e in calendar_events[:3]])
            calendar_context = f"\n\nUpcoming events:\n{event_list}"

        system_prompt = f"""You are UniMind, a compassionate AI wellness companion for college students.

Remember small personal details (like name, mood, or achievements) naturally.
Current emotional tone: {emotion} (intensity: {intensity}/1.0).{calendar_context}

Be warm, empathetic, and concise (2–3 sentences)."""

        # ✅ Debug before OpenRouter call
        print("🚀 Sending to OpenRouter with", len(recent_history), "messages")

        ai_response = "I'm here for you."  # default fallback
        if OPENROUTER_API_KEY:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "anthropic/claude-3.5-sonnet",
                    "messages": [{"role": "system", "content": system_prompt}] + recent_history,
                    "max_tokens": 200,
                },
                timeout=25,
            )
            print("🛰️ OpenRouter status:", response.status_code)  # ✅ Debug 3

            if response.status_code == 200:
                result = response.json()
                ai_response = (
                    result.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", ai_response)
                )
            else:
                print(f"⚠️ OpenRouter error: {response.status_code}")
        else:
            print("⚠️ Missing OPENROUTER_API_KEY — fallback to offline")

        # Save chat
        chat_entry = {
            "user_message": user_message,
            "ai_response": ai_response,
            "emotion": emotion_data,
            "timestamp": datetime.now().isoformat(),
        }
        

        if firebase_db:
            firebase_db.collection("users").document(user_id).collection("chats").add(chat_entry)

        return jsonify({
            "response": ai_response,
            "emotion": emotion_data,
            "timestamp": chat_entry["timestamp"],
        }), 200

    except Exception as e:
        print("❌ Chat error:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/api/chat/history", methods=["GET"])
def get_chat_history():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    try:
        chats_ref = firebase_db.collection("users").document(user_id).collection("chats")
        docs = chats_ref.order_by("timestamp").stream()
        history = [doc.to_dict() for doc in docs]
        return jsonify({"messages": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# Emotion Detection (Blossoms.ai)
# -----------------------------------------------------------
def detect_emotion(message):
    if not BLOSSOMS_API_KEY:
        return {
            "emotion": "neutral",
            "intensity": 0.5,
            "confidence": 0.7,
            "note": "Using mock data - add BLOSSOMS_API_KEY to environment"
        }

    try:
        response = requests.post(
            'https://api.blossoms.ai/v1/analyze',
            headers={
                'Authorization': f'Bearer {BLOSSOMS_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={'text': message},
            timeout=10
        )
        return response.json() if response.status_code == 200 else {"emotion": "neutral"}
    except Exception as e:
        return {"emotion": "neutral", "note": f"Error: {e}"}

# -----------------------------------------------------------
# AI Response Generation (OpenRouter)
# -----------------------------------------------------------
def generate_empathetic_response(message, emotion_data, calendar_events=[]):
    if not OPENROUTER_API_KEY:
        return f"I hear you. It sounds like you're feeling {emotion_data.get('emotion', 'thoughtful')} right now. I'm here to support you. (Add OPENROUTER_API_KEY to enable full AI responses)"

    try:
        emotion = emotion_data.get('emotion', 'neutral')
        intensity = emotion_data.get('intensity', 0.5)
        calendar_context = ""

        if calendar_events:
            event_list = "\n".join([f"- {e['title']} on {e['date']}" for e in calendar_events[:3]])
            calendar_context = f"\n\nUpcoming events:\n{event_list}"

        system_prompt = f"""You are UniMind, a compassionate AI mental wellness companion for college students.

Current emotional state: The student seems to be feeling {emotion} (intensity: {intensity}/1.0).{calendar_context}

Guidelines:
- Be warm, empathetic, and supportive
- Keep responses concise (2-3 sentences)
- Acknowledge their emotions
- Offer gentle suggestions
- Reference calendar events if relevant
- Use a calm tone
"""

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://unimind.app',
                'X-Title': 'UniMind'
            },
            json={
                'model': 'anthropic/claude-3.5-sonnet',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': message}
                ],
                'max_tokens': 150
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        return f"I'm here for you. It sounds like you're experiencing {emotion}."

    except Exception as e:
        return f"I sense you might be feeling {emotion_data.get('emotion', 'stressed')}. I'm here to listen and support you."

# -----------------------------------------------------------
# Journal Entries
# -----------------------------------------------------------
@app.route('/api/journal', methods=['POST'])
def add_journal_entry():
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        entry = {
            "mood": data.get('mood'),
            "mood_text": data.get('mood_text', ''),
            "date": data.get('date', datetime.now().strftime("%Y-%m-%d")),
            "timestamp": datetime.now().isoformat(),
        }

        # Save to Firestore under /users/{user_id}/journals/
        doc_ref = firebase_db.collection('users').document(user_id).collection('journals').add(entry)

        # doc_ref[1].id returns the generated document ID
        return jsonify({
            "message": "Journal entry saved",
            "id": doc_ref[1].id,
            "entry": entry
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/journal', methods=['GET'])
def get_journal_entries():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        # Get all entries for this user
        journals_ref = firebase_db.collection('users').document(user_id).collection('journals')
        docs = journals_ref.stream()

        entries = []
        for doc in docs:
            entry = doc.to_dict()
            entry["id"] = doc.id  # ✅ Include the Firestore document ID
            entries.append(entry)

        # Sort newest → oldest
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return jsonify({"entries": entries, "count": len(entries)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
# Delete Journal Entry
# -----------------------------------------------------------
@app.route('/api/journal/<entry_id>', methods=['DELETE'])
def delete_journal_entry(entry_id):
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        entry_ref = firebase_db.collection('users').document(user_id).collection('journals').document(entry_id)
        doc = entry_ref.get()
        if not doc.exists:
            return jsonify({"error": "Entry not found"}), 404

        entry_ref.delete()
        return jsonify({"success": True, "deleted_id": entry_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------
# Nationwide + School-Specific Mental Health Resources
# -----------------------------------------------------------
@app.route('/api/resources', methods=['GET'])
def get_resources():
    school = request.args.get('school', '').strip()

    # Always show nationwide resources
    global_resources = [
        {
            "name": "988 Suicide & Crisis Lifeline",
            "description": "Free and confidential support for people in distress, 24/7 across the U.S.",
            "url": "https://988lifeline.org"
        },
        {
            "name": "Crisis Text Line",
            "description": "Text HOME to 741741 to connect with a trained crisis counselor (U.S. & Canada).",
            "url": "https://www.crisistextline.org"
        },
        {
            "name": "7 Cups",
            "description": "Free emotional support from trained listeners, plus affordable online therapy.",
            "url": "https://www.7cups.com"
        },
        {
            "name": "SAMHSA National Helpline",
            "description": "24/7 treatment referral and information for mental health or substance use issues.",
            "url": "https://findtreatment.gov"
        }
    ]

    # If no school provided, return just global and an empty local list
    if not school:
        return jsonify({
            "global": global_resources,
            "local": [],
            "school_specific": []   # backward compatibility with old frontend key
        }), 200

    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
    if not GOOGLE_PLACES_API_KEY:
        # If key missing, avoid crashing; return global only
        return jsonify({
            "global": global_resources,
            "local": [],
            "school_specific": [],
            "error": "GOOGLE_PLACES_API_KEY not set on server"
        }), 200

    try:
        # 1) Geocode the college name to lat/lng
        geo = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": school, "key": GOOGLE_PLACES_API_KEY},
            timeout=10
        ).json()

        if not geo.get("results"):
            return jsonify({
                "global": global_resources,
                "local": [],
                "school_specific": [],
                "note": f"No geocoding results for '{school}'"
            }), 200

        loc = geo["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]

        # 2) Search nearby mental-health resources (within ~15km / ~9mi)
        places = requests.get(
            "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
            params={
                "location": f"{lat},{lng}",
                "radius": 15000,
                "keyword": "mental health OR counseling OR therapy OR wellness",
                "key": GOOGLE_PLACES_API_KEY,
            },
            timeout=10
        ).json()

        local_resources = []
        for p in places.get("results", []):
            local_resources.append({
                "name": p.get("name"),
                "address": p.get("vicinity"),
                "rating": p.get("rating"),
                "url": f"https://www.google.com/maps/place/?q=place_id:{p.get('place_id')}"
            })

        # Return both 'local' and 'school_specific' to avoid breaking the current UI
        return jsonify({
            "global": global_resources,
            "local": local_resources,
            "school_specific": local_resources
        }), 200

    except Exception as e:
        return jsonify({
            "global": global_resources,
            "local": [],
            "school_specific": [],
            "error": str(e)
        }), 500

# -----------------------------------------------------------
# Calendar Mock Data
# -----------------------------------------------------------
@app.route('/api/calendar/events', methods=['GET'])
def get_calendar_events():
    mock_events = [
        {"title": "History Exam", "date": "April 25", "time": "10:00 AM"},
        {"title": "Presentation Discussion", "date": "April 20", "time": "1:00 PM"},
        {"title": "Physics Exam", "date": "April 21", "time": "10:00 AM"}
    ]
    return jsonify({"events": mock_events}), 200

# -----------------------------------------------------------
# Firebase Test Route
# -----------------------------------------------------------
@app.route('/api/firebase-test', methods=['GET'])
def firebase_test():
    try:
        if not firebase_db:
            return jsonify({"status": "error", "message": "Firebase not initialized"}), 500

        test_data = {
            "message": "Hello from Flask!",
            "timestamp": datetime.now().isoformat()
        }
        firebase_db.collection('test_connection').add(test_data)
        return jsonify({"status": "success", "message": "Data written to Firestore"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# -----------------------------------------------------------
# Run Server
# -----------------------------------------------------------
if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=8000, debug=debug_mode)
