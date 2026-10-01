import { useState } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar";
import Home from "./components/Home";
import UploadDNA from "./components/UploadDNA";
import MutationResults from "./components/MutationResult";
import History from "./components/History";
import HistoryDetail from "./components/HistoryDetail";

// --- Auth (new) ---
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./components/Login";
import Register from "./components/Register";

import { analyzeSequences } from "./api/dnaApi";

import "./App.css";

// Historical records are cached in localStorage so they survive a refresh.
// This is separate from the browser's *navigation* History API (used by
// react-router below) - this is just where we persist past reports.
const STORAGE_KEY = "dnaHistory";

function loadStoredHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.warn("Could not read saved history, starting fresh:", err);
    return [];
  }
}

function AppContent() {
  const navigate = useNavigate();
  const location = useLocation();

  // Hide the Navbar on the login / register screens (new)
  const isAuthPage =
    location.pathname === "/login" || location.pathname === "/register";

  const [mutations, setMutations] = useState([]);
  const [history, setHistory] = useState(loadStoredHistory);

  // API result handling state
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState("");
  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  const saveHistory = (updatedHistory) => {
    setHistory(updatedHistory);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedHistory));
  };

  const analyzeDNA = async (reference, sample) => {
    setIsLoading(true);
    setApiError("");

    try {
      const results = await analyzeSequences(reference, sample);

      setMutations(results);
      setHasAnalyzed(true);

      const report = {
        id: Date.now(),
        date: new Date().toISOString(),
        reference,
        sample,
        referenceLength: reference.length,
        sampleLength: sample.length,
        mutationCount: results.length,
        mutations: results,
        status: results.length > 0 ? "Mutations Found" : "No Mutations",
      };

      setHistory((previousHistory) => {
        const updatedHistory = [report, ...previousHistory].slice(0, 25);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedHistory));
        return updatedHistory;
      });

      // Jump the user straight to the Results page once analysis finishes
      navigate("/results");
    } catch (err) {
      // analyzeSequences already falls back locally on network/API errors,
      // so this only fires for genuinely unexpected failures.
      setApiError(
        "Something went wrong while analyzing the sequences. Please try again."
      );
      console.error(err);

      // Record the failed attempt too, so History gives an honest picture
      // of every run (this is what drives the "Failed" status filter).
      const failedReport = {
        id: Date.now(),
        date: new Date().toISOString(),
        reference,
        sample,
        referenceLength: reference.length,
        sampleLength: sample.length,
        mutationCount: 0,
        mutations: [],
        status: "Failed",
      };

      setHistory((previousHistory) => {
        const updatedHistory = [failedReport, ...previousHistory].slice(0, 25);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedHistory));
        return updatedHistory;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = () => {
    saveHistory([]);
  };

  return (
    <>
      {!isAuthPage && <Navbar />}

      <Routes>
        {/* Public routes (new) */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Protected routes: require login */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home
                hasAnalyzed={hasAnalyzed}
                isLoading={isLoading}
                mutationCount={mutations.length}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <UploadDNA onAnalyze={analyzeDNA} isLoading={isLoading} />
            </ProtectedRoute>
          }
        />

        <Route
          path="/results"
          element={
            <ProtectedRoute>
              <MutationResults
                mutations={mutations}
                isLoading={isLoading}
                error={apiError}
                hasAnalyzed={hasAnalyzed}
              />
            </ProtectedRoute>
          }
        />

        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History history={history} onClear={clearHistory} />
            </ProtectedRoute>
          }
        />

        {/* Selected-report view, reached via the "View" action in History */}
        <Route
          path="/history/:id"
          element={
            <ProtectedRoute>
              <HistoryDetail history={history} />
            </ProtectedRoute>
          }
        />
      </Routes>
    </>
  );
}

// AuthProvider wraps everything so any component can call useAuth()
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
