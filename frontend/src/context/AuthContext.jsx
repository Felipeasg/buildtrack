import { createContext, useContext } from "react";

const AuthContext = createContext(null);

// Auth is disabled for local testing: the app runs as a fixed demo user
// (matching the backend default) with no login step.
const DEMO_USER = { email: "demo@buildtrack.local", full_name: "Demo User" };

export function AuthProvider({ children }) {
  const logout = () => {};

  return (
    <AuthContext.Provider value={{ user: DEMO_USER, loading: false, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
