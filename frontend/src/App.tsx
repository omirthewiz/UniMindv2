import React from 'react';
import './App.css';

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-lavender-50 to-gold-50">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-sage-800 mb-4">
            🧠 UniMind
          </h1>
          <p className="text-2xl text-lavender-600 mb-8">
            AI-Powered Mental Wellness Companion
          </p>
          <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
            <p className="text-gray-700 mb-4">
              Welcome to UniMind, your supportive companion for managing stress, anxiety, and burnout.
            </p>
            <p className="text-gray-600 text-sm">
              Features coming soon: AI Chat, Mood Journaling, UniQuest Board, and more!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
