# UniMind v2 - AI-Powered Mental Wellness Platform

## Overview
UniMind is an AI-powered mental wellness web application designed specifically for college students to help manage stress, anxiety, and burnout through empathetic AI conversations, schedule-aware check-ins, mood journaling, and gamified wellness tracking.

## Tech Stack
- **Frontend**: React (TypeScript) with Tailwind CSS
- **Backend**: Flask (Python 3.11)
- **AI Services**: Blossoms.ai (emotion detection) + OpenRouter (GPT-4/Claude responses)
- **Auth**: Auth0 (Google + Email login)
- **Calendar**: Google Calendar API integration
- **Database**: Firebase/Supabase (for user profiles, journal entries, chat history)
- **Hosting**: Replit

## Project Structure
```
/
├── backend/
│   ├── app.py              # Flask API server
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── Dashboard.tsx  # Main dashboard component
│   │   ├── App.tsx         # App entry point
│   │   └── index.css       # Tailwind CSS imports
│   ├── package.json        # Node dependencies
│   └── tailwind.config.js  # Custom sage/lavender/gold theme
└── replit.md              # This file
```

## Core Features (MVP)
1. **AI Chat Interface**: Emotion-aware conversations combining Blossoms.ai sentiment analysis with OpenRouter's empathetic responses
2. **Mood Journaling**: Daily mood tracking with emoji-based check-ins
3. **Calendar Integration**: Schedule-aware prompts using Google Calendar API
4. **Resource Center**: Global and school-specific mental health resources
5. **UniQuest Board**: Gamified wellness tracking system (in development)
6. **Auth0 Integration**: Secure authentication with Google/Email login

## API Endpoints
- `GET /api/health` - Health check
- `POST /api/chat` - AI conversation endpoint (Blossoms.ai + OpenRouter)
- `POST /api/journal` - Log mood entry
- `GET /api/journal` - Retrieve journal entries
- `GET /api/resources` - Get mental health resources (global + school-specific)
- `GET /api/calendar/events` - Get upcoming calendar events
- `GET /api/uniquest/progress` - UniQuest Board progress
- `GET /api/uniquest/reflection-card` - AI-generated affirmations
- `POST /api/profile` - Save user profile
- `GET /api/profile` - Get user profile

## Environment Variables
Stored in Replit Secrets:
- `BLOSSOMS_API_KEY` - For emotion detection
- `OPENROUTER_API_KEY` - For AI responses
- `GOOGLE_CLIENT_ID` - Calendar API
- `GOOGLE_CLIENT_SECRET` - Calendar API
- `AUTH0_DOMAIN` - Authentication
- `AUTH0_CLIENT_ID` - Authentication
- `AUTH0_CLIENT_SECRET` - Authentication

## Design System
- **Color Palette**: Sage, Lavender, and Gold (pastel theme for calm, supportive aesthetic)
- **Typography**: System fonts for readability
- **UI/UX**: Clean, minimal design focused on mental wellness

## Recent Changes (Nov 8, 2025)
- Initial project setup with Flask backend and React frontend
- Implemented AI chat pipeline (Blossoms.ai → OpenRouter)
- Created Dashboard UI with mood tracker, chat interface, and calendar events
- Configured Tailwind CSS with custom wellness color palette
- Set up API endpoints for chat, journaling, resources, and calendar
- Added environment variables for all API integrations

## Next Steps
- Complete Auth0 integration for user authentication
- Implement Firebase/Supabase for persistent data storage
- Build UniQuest Board gamification system
- Add Google Calendar OAuth integration
- Create Resources page with school-specific filtering
- Implement weekly AI-generated mood summaries
- Add crisis detection and resource suggestions

## Notes
- Using mock calendar data until Google Calendar OAuth is fully integrated
- In-memory storage for chat/journal (will migrate to Firebase)
- Demo user mode enabled for testing without authentication
