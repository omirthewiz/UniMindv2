import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)
CORS(app)

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
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        user_id = data.get('user_id', 'demo_user')
        calendar_events = data.get('calendar_events', [])

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        emotion_data = detect_emotion(user_message)
        ai_response = generate_empathetic_response(user_message, emotion_data, calendar_events)

        chat_entry = {
            "user_message": user_message,
            "ai_response": ai_response,
            "emotion": emotion_data,
            "timestamp": datetime.now().isoformat()
        }

        if user_id not in chat_sessions:
            chat_sessions[user_id] = []
        chat_sessions[user_id].append(chat_entry)

        # Save chat to Firestore (optional)
        if firebase_db:
            firebase_db.collection('chats').add({
                "user_id": user_id,
                **chat_entry
            })

        return jsonify({
            "response": ai_response,
            "emotion": emotion_data,
            "timestamp": chat_entry["timestamp"]
        }), 200

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
        user_id = data.get('user_id', 'demo_user')
        mood = data.get('mood')
        mood_text = data.get('mood_text', '')

        if not mood:
            return jsonify({"error": "Mood is required"}), 400

        entry = {
            "mood": mood,
            "mood_text": mood_text,
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d")
        }

        if user_id not in journal_entries:
            journal_entries[user_id] = []
        journal_entries[user_id].append(entry)

        # Save to Firestore if connected
        if firebase_db:
            firebase_db.collection('journals').add({
                "user_id": user_id,
                **entry
            })

        return jsonify({"message": "Journal entry saved", "entry": entry}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/journal', methods=['GET'])
def get_journal_entries():
    try:
        user_id = request.args.get('user_id', 'demo_user')
        days = int(request.args.get('days', 30))
        entries = journal_entries.get(user_id, [])
        cutoff_date = datetime.now() - timedelta(days=days)
        recent = [e for e in entries if datetime.fromisoformat(e['timestamp']) > cutoff_date]

        return jsonify({"entries": recent, "count": len(recent)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
# Nationwide + School-Specific Mental Health Resources
# -----------------------------------------------------------
@app.route('/api/resources', methods=['GET'])
def get_resources():
    school = request.args.get('school', '').strip()

    # Global nationwide resources (always shown)
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
            "description": "24/7 treatment referral and information for individuals facing mental health or substance use issues.",
            "url": "https://findtreatment.gov"
        }
    ]

    # Local / campus-specific section
    if not school:
        school_specific = [{
            "name": "Select your school",
            "description": "Enter your school name above to see campus-specific resources."
        }]
    else:
        school_specific = get_school_resources(school)

    return jsonify({
        "global": global_resources,
        "school_specific": school_specific
    }), 200


def get_school_resources(school):
    """Return custom resource data for known schools, else generic fallback."""
    school_lower = school.lower()

    if "buffalo" in school_lower or "ub" in school_lower:
        return [
            {
                "name": "UB Counseling Services",
                "description": "Provides free, confidential counseling and therapy to UB students.",
                "url": "https://www.buffalo.edu/studentlife/who-we-are/departments/counseling.html"
            },
            {
                "name": "Crisis Services of Erie County",
                "description": "24-hour crisis hotline and mobile outreach for mental health emergencies.",
                "url": "https://crisisservices.org/"
            }
        ]
    elif "mit" in school_lower:
        return [
            {
                "name": "MIT Student Mental Health & Counseling",
                "description": "Support for MIT students' emotional and psychological well-being.",
                "url": "https://medical.mit.edu/mental-health"
            }
        ]
    elif "ucla" in school_lower:
        return [
            {
                "name": "UCLA Counseling & Psychological Services (CAPS)",
                "description": "Provides mental health support and workshops for UCLA students.",
                "url": "https://www.counseling.ucla.edu/"
            }
        ]
    else:
        return [
            {
                "name": f"{school} Counseling Center",
                "description": "Campus mental health services and support.",
                "url": "#"
            }
        ]

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
