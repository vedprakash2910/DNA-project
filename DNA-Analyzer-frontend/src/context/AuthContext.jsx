import { createContext, useContext, useEffect, useState } from "react";

const USERS_KEY = "dna_users";
const SESSION_KEY = "dna_session";

const AuthContext = createContext(null);

// Hash passwords so they are never stored as plain text.
// (Still demo-grade security: everything lives in the browser.)
async function hashPassword(password) {
  const data = new TextEncoder().encode(password);
  const buf = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function readUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY)) || [];
  } catch {
    return [];
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore session on page refresh
  useEffect(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(SESSION_KEY));
      if (saved) setUser(saved);
    } catch {
      /* ignore corrupted session */
    }
    setLoading(false);
  }, []);

  const register = async ({ name, email, password }) => {
    const users = readUsers();
    const normalized = email.trim().toLowerCase();

    if (users.some((u) => u.email === normalized)) {
      throw new Error("An account with this email already exists.");
    }

    const newUser = {
      id: crypto.randomUUID(),
      name: name.trim(),
      email: normalized,
      passwordHash: await hashPassword(password),
    };
    localStorage.setItem(USERS_KEY, JSON.stringify([...users, newUser]));

    const session = { id: newUser.id, name: newUser.name, email: newUser.email };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    setUser(session);
  };

  const login = async ({ email, password }) => {
    const users = readUsers();
    const normalized = email.trim().toLowerCase();
    const found = users.find((u) => u.email === normalized);
    const hash = await hashPassword(password);

    if (!found || found.passwordHash !== hash) {
      throw new Error("Invalid email or password.");
    }

    const session = { id: found.id, name: found.name, email: found.email };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
    setUser(session);
  };

  const logout = () => {
    localStorage.removeItem(SESSION_KEY);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
};
