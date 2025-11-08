import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import json

app = Flask(__name__)
CORS(app)

BLOSSOMS_API_KEY = os.environ.get('BLOSSOMS_API_KEY')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

chat_sessions = {}
journal_entries = {}
user_profiles = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "UniMind API is running"}), 200

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
        
        ai_response = generate_empathetic_response(
            user_message, 
            emotion_data, 
            calendar_events
        )
        
        chat_entry = {
            "user_message": user_message,
            "ai_response": ai_response,
            "emotion": emotion_data,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id not in chat_sessions:
            chat_sessions[user_id] = []
        chat_sessions[user_id].append(chat_entry)
        
        return jsonify({
            "response": ai_response,
            "emotion": emotion_data,
            "timestamp": chat_entry["timestamp"]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "emotion": "neutral",
                "intensity": 0.5,
                "confidence": 0.5,
                "note": f"Blossoms API error: {response.status_code}"
            }
    except Exception as e:
        return {
            "emotion": "neutral",
            "intensity": 0.5,
            "confidence": 0.5,
            "note": f"Error: {str(e)}"
        }

def generate_empathetic_response(message, emotion_data, calendar_events=[]):
    if not OPENROUTER_API_KEY:
        return f"I hear you. It sounds like you're feeling {emotion_data.get('emotion', 'thoughtful')} right now. I'm here to support you. (Add OPENROUTER_API_KEY to enable full AI responses)"
    
    try:
        emotion = emotion_data.get('emotion', 'neutral')
        intensity = emotion_data.get('intensity', 0.5)
        
        calendar_context = ""
        if calendar_events:
            event_list = "\n".join([f"- {event['title']} on {event['date']}" for event in calendar_events[:3]])
            calendar_context = f"\n\nUpcoming events:\n{event_list}"
        
        system_prompt = f"""You are UniMind, a compassionate AI mental wellness companion for college students. 

Current emotional state: The student seems to be feeling {emotion} (intensity: {intensity}/1.0).{calendar_context}

Guidelines:
- Be warm, empathetic, and supportive
- Keep responses concise (2-3 sentences)
- Acknowledge their emotions
- Offer gentle suggestions for coping strategies when appropriate
- Reference their calendar events if relevant to their stress
- Use a calm, understanding tone
- Never be clinical or overly formal"""

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://unimind.replit.app',
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
        else:
            return f"I'm here for you. It sounds like you're experiencing {emotion}. Would you like to talk more about what's on your mind?"
            
    except Exception as e:
        return f"I sense you might be feeling {emotion_data.get('emotion', 'stressed')}. I'm here to listen and support you through this."

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
        
        return jsonify({
            "message": "Journal entry saved",
            "entry": entry
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/journal', methods=['GET'])
def get_journal_entries():
    try:
        user_id = request.args.get('user_id', 'demo_user')
        days = int(request.args.get('days', 30))
        
        entries = journal_entries.get(user_id, [])
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_entries = [
            e for e in entries 
            if datetime.fromisoformat(e['timestamp']) > cutoff_date
        ]
        
        return jsonify({
            "entries": recent_entries,
            "count": len(recent_entries)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/resources', methods=['GET'])
def get_resources():
    school = request.args.get('school', '')
    category = request.args.get('category', 'all')
    
    resources = {
        "global": [
            {
                "name": "988 Suicide & Crisis Lifeline",
                "description": "24/7 crisis support via call, text, or chat",
                "contact": "Call or text 988",
                "url": "https://988lifeline.org",
                "category": "crisis"
            },
            {
                "name": "Crisis Text Line",
                "description": "Free 24/7 text-based crisis support",
                "contact": "Text HOME to 741741",
                "url": "https://www.crisistextline.org",
                "category": "crisis"
            },
            {
                "name": "7 Cups",
                "description": "Free emotional support and online therapy",
                "contact": "Online chat",
                "url": "https://www.7cups.com",
                "category": "therapy"
            },
            {
                "name": "NAMI",
                "description": "National Alliance on Mental Illness support",
                "contact": "Call 1-800-950-6264",
                "url": "https://www.nami.org",
                "category": "support"
            },
            {
                "name": "BetterHelp",
                "description": "Affordable online therapy platform",
                "contact": "Online",
                "url": "https://www.betterhelp.com",
                "category": "therapy"
            }
        ],
        "school_specific": get_school_resources(school)
    }
    
    return jsonify(resources), 200

def get_school_resources(school):
    school_lower = school.lower() if school else ""
    
    if not school:
        return [{
            "name": "Select your school",
            "description": "Choose your school to see campus-specific mental health resources",
            "contact": "",
            "url": "",
            "category": "info"
        }]
    
    return [
        {
            "name": f"{school} Counseling Center",
            "description": "Campus mental health and counseling services",
            "contact": "Visit student services",
            "url": "#",
            "category": "counseling"
        },
        {
            "name": f"{school} Student Wellness",
            "description": "Wellness programs and stress management",
            "contact": "Check student portal",
            "url": "#",
            "category": "wellness"
        },
        {
            "name": f"{school} Peer Support",
            "description": "Student-led mental health peer support groups",
            "contact": "Student activities office",
            "url": "#",
            "category": "support"
        }
    ]

@app.route('/api/calendar/events', methods=['GET'])
def get_calendar_events():
    user_id = request.args.get('user_id', 'demo_user')
    
    mock_events = [
        {
            "title": "History Exam",
            "date": "April 25",
            "time": "10:00 AM",
            "type": "exam"
        },
        {
            "title": "Presentation discussion",
            "date": "April 20",
            "time": "1:00 PM",
            "type": "class"
        },
        {
            "title": "Physics exam",
            "date": "April 21",
            "time": "10:00 AM",
            "type": "exam"
        }
    ]
    
    return jsonify({"events": mock_events}), 200

@app.route('/api/uniquest/progress', methods=['GET'])
def get_uniquest_progress():
    user_id = request.args.get('user_id', 'demo_user')
    
    progress = {
        "current_position": 5,
        "total_tiles": 20,
        "badges_earned": 2,
        "reflections_completed": 8,
        "current_streak": 3
    }
    
    return jsonify(progress), 200

@app.route('/api/uniquest/reflection-card', methods=['GET'])
def get_reflection_card():
    if not OPENROUTER_API_KEY:
        affirmations = [
            "You are capable of amazing things.",
            "Taking care of yourself is a priority, not a luxury.",
            "Every small step forward is progress.",
            "You are stronger than you think.",
            "It's okay to take a break when you need it."
        ]
        import random
        return jsonify({
            "affirmation": random.choice(affirmations),
            "type": "daily"
        }), 200
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENROUTER_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'anthropic/claude-3.5-sonnet',
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Generate a short, uplifting affirmation for a college student (1-2 sentences). Make it warm, genuine, and encouraging.'
                    },
                    {
                        'role': 'user',
                        'content': 'Give me a daily affirmation.'
                    }
                ],
                'max_tokens': 50
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            affirmation = result['choices'][0]['message']['content']
        else:
            affirmation = "You are doing your best, and that's more than enough."
            
        return jsonify({
            "affirmation": affirmation,
            "type": "ai_generated"
        }), 200
        
    except Exception as e:
        return jsonify({
            "affirmation": "Take a deep breath. You've got this.",
            "type": "fallback"
        }), 200

@app.route('/api/profile', methods=['POST'])
def save_profile():
    try:
        data = request.json
        user_id = data.get('user_id', 'demo_user')
        
        user_profiles[user_id] = {
            "name": data.get('name', ''),
            "school": data.get('school', ''),
            "updated_at": datetime.now().isoformat()
        }
        
        return jsonify({
            "message": "Profile saved",
            "profile": user_profiles[user_id]
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    user_id = request.args.get('user_id', 'demo_user')
    profile = user_profiles.get(user_id, {
        "name": "Emily",
        "school": "",
        "updated_at": datetime.now().isoformat()
    })
    
    return jsonify(profile), 200

if __name__ == '__main__':
    import os
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=8000, debug=debug_mode)
