import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet } from "react-router-dom"; 
// NOTE: Renamed the import to match the corrected export in DashboardPage.tsx
import DashboardPage from "./components/Dashboard"; 
import Resources from "./pages/Resources";
import Login from "./pages/Login";
import Journal from "./pages/Journal"; // Kept the Journal import from HEAD
import Calendar from "./pages/Calendar"; // Kept the Calendar import from calendar-sidebar

import "./App.css";

// --- MainLayout Component (Correct for Routing with Outlet) ---
// This component renders the persistent sidebar and the <Outlet /> where children will appear.
const MainLayout: React.FC = () => { 
    const { logout, user } = useAuth0();
    const navigate = useNavigate();
    const path = window.location.pathname;

    // Helper function to handle pages that aren't yet fully implemented
    const handleNavigation = (to: string, isComingSoon: boolean, pageName: string) => {
        if (isComingSoon) {
            // Note: Since you cannot use window.alert/confirm, this is a placeholder. 
            // In a real app, you'd show a custom modal notification.
            console.log(`${pageName} page coming soon!`);
        } else {
            navigate(to);
        }
    };
    
    const NavLink = ({ to, label, onClick }: { to: string; label: string; onClick: () => void; }) => (
        <div
            onClick={onClick}
            className={`px-4 py-3 rounded-lg font-medium cursor-pointer transition ${
                path === to || (to === '/' && path === '/') 
                    ? 'bg-sage-100 text-sage-800' 
                    : 'text-sage-600 hover:bg-sage-50'
            }`}
        >
            {label}
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-sage-50 via-lavender-50 to-gold-50">
            <div className="flex">
                {/* Sidebar: Persistent structure */}
                <aside className="w-64 bg-white border-r border-sage-200 min-h-screen p-6">
                    <div className="flex items-center mb-8">
                        <div className="text-3xl mr-2">🧠</div>
                        <h1 className="text-2xl font-bold text-sage-800">UniMind</h1>
                    </div>
                    <nav className="space-y-2">
                        {/* Navigation Links using the unified navigate function */}
                        <NavLink to="/" label="Dashboard" onClick={() => navigate("/")} />
                        <NavLink to="/journal" label="Journal" onClick={() => navigate("/journal")} />
                        <NavLink to="/calendar" label="Calendar" onClick={() => navigate("/calendar")} />
                        <NavLink to="/resources" label="Resources" onClick={() => navigate("/resources")} />
                    </nav>
                    
                     <div className="mt-8 pt-6 border-t border-sage-100">
                        <div className="flex items-center justify-between mb-4">
                            {user?.picture && (
                                <img
                                    src={user.picture}
                                    alt="Profile"
                                    className="w-8 h-8 rounded-full border border-sage-300 shadow-sm"
                                />
                            )}
                            <button
                                onClick={() => logout({ logoutParams: { returnTo: window.location.origin } })}
                                className="px-3 py-1 text-sm bg-lavender-400 hover:bg-lavender-500 text-white rounded-lg shadow-sm transition"
                            >
                                Logout
                            </button>
                        </div>
                    </div>
                </aside>

                {/* The Outlet renders the content of the nested routes */}
                <main className="flex-1 p-8">
                    <Outlet /> 
                </main>
            </div>
        </div>
    );
};
// --- End MainLayout Component ---


function App() {
  const { isAuthenticated, isLoading } = useAuth0();
  console.log("Auth0 context loaded:", isAuthenticated, isLoading);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen text-lg text-gray-600">
        Loading UniMind... 🌸
      </div>
    );
  }

  return (
    <Router>
      {isAuthenticated ? (
        <Routes>
          {/* 1. Parent Route: Uses MainLayout and applies it to all children */}
          <Route path="/" element={<MainLayout />}>
            
            {/* 2. Nested Children (Content renders in the Outlet) */}
            <Route index element={<DashboardPage />} /> {/* Route for / */}
            <Route path="calendar" element={<Calendar />} />
            <Route path="resources" element={<Resources />} />
            <Route path="journal" element={<Journal />} /> {/* Added Journal route */}

            {/* Fallback route within the layout */}
            <Route path="*" element={<DashboardPage />} /> 

          </Route>
        </Routes>
      ) : (
        <Login />
      )}
    </Router>
  );
}

export default App;