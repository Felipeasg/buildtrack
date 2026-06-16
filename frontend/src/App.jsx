import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import MilestoneDetail from "./pages/MilestoneDetail";

function TopBar() {
  const { user, logout } = useAuth();
  return (
    <div className="topbar">
      <a href="/" className="brand">
        <span className="tick" />
        BuildTrack
        <span className="sub">Home Build</span>
      </a>
      <div className="topbar-right">
        <span className="user-chip">{user?.full_name || user?.email}</span>
        <button className="btn btn-sm btn-ghost" onClick={logout}>Sign out</button>
      </div>
    </div>
  );
}

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="container"><p style={{ color: "var(--muted)" }}>Loading…</p></div>;
  if (!user) return <Navigate to="/login" replace />;
  return (
    <div className="app-shell">
      <TopBar />
      {children}
    </div>
  );
}

function PublicOnly({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
          <Route path="/" element={<Protected><Dashboard /></Protected>} />
          <Route path="/milestones/:id" element={<Protected><MilestoneDetail /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}
