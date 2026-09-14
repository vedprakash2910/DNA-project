import { useState } from "react";

import Navbar from "./components/Navbar";
import Home from "./components/Home";
import UploadDNA from "./components/UploadDNA";
import MutationResults from "./components/MutationResult";
import History from "./components/History";

import "./App.css";

function App() {
  const [mutations, setMutations] = useState([]);
  const [history, setHistory] = useState([]);

  const analyzeDNA = (reference, sample) => {
    const results = [];

    const maxLength = Math.max(
      reference.length,
      sample.length
    );

    for (let i = 0; i < maxLength; i++) {
      const original = reference[i] || "-";
      const mutated = sample[i] || "-";

      if (original !== mutated) {
        let type = "Substitution";

        if (original === "-") {
          type = "Insertion";
        } else if (mutated === "-") {
          type = "Deletion";
        }

        results.push({
          type: type,
          position: i + 1,
          original: original,
          mutated: mutated
        });
      }
    }

    setMutations(results);

    const report = {
      id: Date.now(),
      date: new Date().toLocaleString(),
      referenceLength: reference.length,
      sampleLength: sample.length,
      mutationCount: results.length
    };

    setHistory((previousHistory) => {
      const updatedHistory = [
        report,
        ...previousHistory
      ].slice(0, 10);

      localStorage.setItem(
        "dnaHistory",
        JSON.stringify(updatedHistory)
      );

      return updatedHistory;
    });

    setTimeout(() => {
      document
        .getElementById("results")
        ?.scrollIntoView({
          behavior: "smooth"
        });
    }, 100);
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("dnaHistory");
  };

  return (
    <>
      <Navbar />

      <Home />

      <UploadDNA
        onAnalyze={analyzeDNA}
      />

      <MutationResults
        mutations={mutations}
      />

      <History
        history={history}
        onClear={clearHistory}
      />
    </>
  );
}

export default App;