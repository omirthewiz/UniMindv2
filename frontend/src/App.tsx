import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { BrowserRouter as Router, Routes, Route, useNavigate, Outlet } from "react-router-dom"; 
import Dashboard from "./components/Dashboard"; 
import Resources from "./pages/Resources";
import Login from "./pages/Login";
<<<<<<< HEAD
import Journal from "./pages/Journal";
=======
import Calendar from "./pages/Calendar"; 

>>>>>>> origin/calendar-sidebar
import "./App.css";

// --- MainLayout Component (Correct for Routing with Outlet) ---
// This component renders the persistent sidebar and the <Outlet /> where children will appear.
const MainLayout: React.FC = () => { 
    const { logout, user } = useAuth0();
    const navigate = useNavigate();
    const path = window.location.pathname;

    const showComingSoon = (pageName: string) => {
        console.error(`${pageName} page coming soon!`);
    };
    
    const NavLink = ({ to, label, isActive, onClick }: { to: string; label: string; isActive: boolean; onClick?: () => void; }) => (
        <div
            onClick={onClick || (() => navigate(to))}
            className={`px-4 py-3 rounded-lg font-medium cursor-pointer transition ${
                isActive 
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
                        <NavLink to="/" label="Dashboard" isActive={path === '/'} />
                        <NavLink to="" label="Journal" isActive={false} onClick={() => showComingSoon('Journal')} />
                        <NavLink to="" label="Check-In" isActive={false} onClick={() => showComingSoon('Check-In')} />
                        <NavLink to="/calendar" label="Calendar" isActive={path === '/calendar'} />
                        <NavLink to="/resources" label="Resources" isActive={path === '/resources'} />
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

                {/* FIX: Use Outlet to render the nested content */}
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
<<<<<<< HEAD
          <Route path="/" element={<Dashboard />} />
          <Route path="/resources" element={<Resources />} />
          <Route path="/journal" element={<Journal />} />
=======
          {/* 1. Parent Route: Uses MainLayout */}
          <Route path="/" element={<MainLayout />}>
            
            {/* 2. Nested Children (Content renders in the Outlet) */}
            <Route index element={<Dashboard />} /> {/* / */}
            <Route path="calendar" element={<Calendar />} />
            <Route path="resources" element={<Resources />} />

            {/* FIX: Use the Dashboard as the fallback page inside the layout */}
            <Route path="*" element={<Dashboard />} /> 

          </Route>
>>>>>>> origin/calendar-sidebar
        </Routes>
      ) : (
        <Login />
      )}
    </Router>
  );
}

export default App;