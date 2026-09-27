// src/api/dnaApi.js
//
// Frontend "API result handling" layer.
//
// This talks to a backend endpoint (POST /api/analyze) that should accept
// { reference, sample } and return { mutations: [...] }.
//
// Until the backend teammate's endpoint is live (or if it's ever offline),
// this automatically falls back to computing mutations locally, so the UI
// keeps working end-to-end. Once the real API is deployed, just set
// VITE_API_URL in a .env file — no component code needs to change.

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api";

// Same diffing logic that used to live in App.jsx, kept here as the
// "offline" fallback and as a stand-in for the backend's algorithm.
function computeMutationsLocally(reference, sample) {
  const results = [];
  const maxLength = Math.max(reference.length, sample.length);

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
        type,
        position: i + 1,
        original,
        mutated,
      });
    }
  }

  return results;
}

/**
 * Sends reference/sample sequences to the backend for analysis.
 * Throws only for truly unexpected client-side errors — network/API
 * failures are handled internally by falling back to local computation
 * so a flaky or not-yet-built backend never breaks the demo.
 *
 * @param {string} reference
 * @param {string} sample
 * @returns {Promise<Array<{type: string, position: number, original: string, mutated: string}>>}
 */
export async function analyzeSequences(reference, sample) {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reference, sample }),
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const data = await response.json();

    // Accept either { mutations: [...] } or a bare array, since the
    // exact backend response shape may still change.
    return Array.isArray(data) ? data : data.mutations ?? [];
  } catch (err) {
    console.warn(
      "DNA analysis API unavailable, falling back to local computation:",
      err.message
    );
    return computeMutationsLocally(reference, sample);
  }
}
