import { useState } from "react";

import Navbar from "./components/Navbar";
import Home from "./components/Home";
import UploadDNA from "./components/UploadDNA";
import MutationResults from "./components/MutationResult";
import History from "./components/History";

import { analyzeSequences } from "./api/dnaApi";

import "./App.css";

function App() {
  const [activeSection, setActiveSection] = useState("home");

  const [mutations, setMutations] = useState([]);
  const [history, setHistory] = useState([]);

  // API result handling state
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState("");
  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  const analyzeDNA = async (reference, sample) => {
    setIsLoading(true);
    setApiError("");

    try {
      const results = await analyzeSequences(reference, sample);

      setMutations(results);
      setHasAnalyzed(true);

      const report = {
        id: Date.now(),
        date: new Date().toLocaleString(),
        referenceLength: reference.length,
        sampleLength: sample.length,
        mutationCount: results.length,
      };

      setHistory((previousHistory) => {
        const updatedHistory = [report, ...previousHistory].slice(0, 10);

        localStorage.setItem("dnaHistory", JSON.stringify(updatedHistory));

        return updatedHistory;
      });

      // Jump the user straight to the Results tab once analysis finishes
      setActiveSection("results");
    } catch (err) {
      // analyzeSequences already falls back locally on network/API errors,
      // so this only fires for genuinely unexpected failures.
      setApiError(
        "Something went wrong while analyzing the sequences. Please try again."
      );
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("dnaHistory");
  };

  return (
    <>
      <Navbar activeSection={activeSection} onNavigate={setActiveSection} />

      {activeSection === "home" && (
        <Home
          onNavigate={setActiveSection}
          hasAnalyzed={hasAnalyzed}
          isLoading={isLoading}
          mutationCount={mutations.length}
        />
      )}

      {activeSection === "upload" && (
        <UploadDNA onAnalyze={analyzeDNA} isLoading={isLoading} />
      )}

      {activeSection === "results" && (
        <MutationResults
          mutations={mutations}
          isLoading={isLoading}
          error={apiError}
          hasAnalyzed={hasAnalyzed}
        />
      )}

      {activeSection === "history" && (
        <History history={history} onClear={clearHistory} />
      )}
    </>
  );
}

export default App;
