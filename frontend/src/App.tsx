import React from "react";
import { useAuth0 } from "@auth0/auth0-react";
import Dashboard from "./components/Dashboard";
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

  return isAuthenticated ? <Dashboard /> : <Login />;
}

export default App;
