import { useState } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";

import Navbar from "./components/Navbar";
import Home from "./components/Home";
import UploadDNA from "./components/UploadDNA";
import MutationResults from "./components/MutationResult";
import History from "./components/History";
import HistoryDetail from "./components/HistoryDetail";

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

function App() {
  const navigate = useNavigate();

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
      <Navbar />

      <Routes>
        <Route
          path="/"
          element={
            <Home
              hasAnalyzed={hasAnalyzed}
              isLoading={isLoading}
              mutationCount={mutations.length}
            />
          }
        />

        <Route
          path="/upload"
          element={<UploadDNA onAnalyze={analyzeDNA} isLoading={isLoading} />}
        />

        <Route
          path="/results"
          element={
            <MutationResults
              mutations={mutations}
              isLoading={isLoading}
              error={apiError}
              hasAnalyzed={hasAnalyzed}
            />
          }
        />

        <Route
          path="/history"
          element={<History history={history} onClear={clearHistory} />}
        />

        {/* Selected-report view, reached via the "View" action in History */}
        <Route
          path="/history/:id"
          element={<HistoryDetail history={history} />}
        />
      </Routes>
    </>
  );
}

export default App;
