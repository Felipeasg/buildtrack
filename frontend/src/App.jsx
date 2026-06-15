import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";
import MilestoneDetail from "./pages/MilestoneDetail";

function TopBar() {
  const { user } = useAuth();
  return (
    <div className="topbar">
      <a href="/" className="brand">
        <span className="tick" />
        BuildTrack
        <span className="sub">Home Build</span>
      </a>
      <div className="topbar-right">
        <span className="user-chip">{user?.full_name || user?.email}</span>
      </div>
    </div>
  );
}

function Shell({ children }) {
  return (
    <div className="app-shell">
      <TopBar />
      {children}
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Shell><Dashboard /></Shell>} />
          <Route path="/milestones/:id" element={<Shell><MilestoneDetail /></Shell>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
