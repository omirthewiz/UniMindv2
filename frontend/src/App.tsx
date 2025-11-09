import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import Resources from "./pages/Resources";
import Login from "./pages/Login";
import "./App.css";

function App() {
  const { isAuthenticated, isLoading } = useAuth0();

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
          <Route path="/" element={<Dashboard />} />
          <Route path="/resources" element={<Resources />} />
        </Routes>
      ) : (
        <Login />
      )}
    </Router>
  );
}

export default App;
