import { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const DEFAULT_API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function App() {
  // state
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const [question, setQuestion] = useState("");
  const [useLlm, setUseLlm] = useState(false);
  const [reply, setReply] = useState("");
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [docLoading, setDocLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [newDocSource, setNewDocSource] = useState("");
  const [newDocText, setNewDocText] = useState("");
  const [indexing, setIndexing] = useState(false);
  const [indexStatus, setIndexStatus] = useState("");

  useEffect(() => {
    loadDocuments();
  }, [apiBase]);

  async function loadDocuments() {
    // step 1 — call GET /api/available-documents
    setDocLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/available-documents`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      // step 2 — update documents state
      setDocuments(data.documents || []);
    } catch (err) {
      // step 3 — show error on failure
      setDocuments([]);
    } finally {
      setDocLoading(false);
    }
  }

  async function askRag(event) {
    // step 1 — prevent default form submit
    event.preventDefault();

    // step 2 — validate question
    if (!question.trim()) {
      setError("Please enter a question.");
      return;
    }
    setError("");
    setLoading(true);
    setReply("");

    try {
      // step 3 — call POST /api/docscan?usellm=true|false
      const res = await fetch(`${apiBase}/api/docscan?usellm=${useLlm}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: question }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // step 4 — show reply
      setReply(data.reply || "");

      // step 5 — add query to history
      setHistory((prev) => [
        {
          id: Date.now(),
          timestamp: new Date().toLocaleTimeString(),
          mode: useLlm ? "LLM" : "retrieval",
          question,
          preview: (data.reply || "").slice(0, 120),
        },
        ...prev.slice(0, 19),
      ]);
    } catch (err) {
      setError(`Request failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function addDocument(event) {
    // step 1 — prevent default form submit
    event.preventDefault();

    // step 2 — validate source and text
    if (!newDocSource.trim()) {
      setIndexStatus("");
      setError("Document source (filename) is required.");
      return;
    }
    if (!newDocText.trim()) {
      setError("Document text is required.");
      return;
    }
    setError("");
    setIndexing(true);
    setIndexStatus("");

    try {
      // step 3 — call POST /api/documents
      const res = await fetch(`${apiBase}/api/documents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source: newDocSource.trim(), text: newDocText }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setIndexStatus(`Indexed: ${data.source} (${data.chunks} chunks)`);

      // step 4 — clear fields
      setNewDocSource("");
      setNewDocText("");

      // step 5 — reload document list
      await loadDocuments();
    } catch (err) {
      setError(`Index failed: ${err.message}`);
    } finally {
      setIndexing(false);
    }
  }

  async function reindexDocuments() {
    // step 1 — call POST /api/reindex
    setDocLoading(true);
    setIndexStatus("");
    try {
      const res = await fetch(`${apiBase}/api/reindex`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      // step 3 — display returned status
      setIndexStatus(
        `Reindexed: ${data.documents} document(s), ${data.chunks} chunk(s)`
      );

      // step 2 — reload document list
      await loadDocuments();
    } catch (err) {
      setError(`Reindex failed: ${err.message}`);
    } finally {
      setDocLoading(false);
    }
  }

  return (
    <div className="app">
      {/* header */}
      <header className="header">
        <h1>Local RAG Workbench</h1>
        <p>
          Index local documents, retrieve relevant chunks, and optionally
          synthesize answers with a local LLM.
        </p>
        <div className="header-controls">
          <div style={{ flex: 1, maxWidth: 400 }}>
            <label htmlFor="api-base">Backend URL</label>
            <input
              id="api-base"
              type="text"
              value={apiBase}
              onChange={(e) => setApiBase(e.target.value.trimEnd())}
              placeholder="http://127.0.0.1:8000"
            />
          </div>
          <button
            type="button"
            className="secondary"
            onClick={loadDocuments}
            disabled={docLoading}
            style={{ alignSelf: "flex-end" }}
          >
            {docLoading ? "Loading..." : "Refresh docs"}
          </button>
        </div>
      </header>

      <div className="layout">
        {/* left column */}
        <div>
          {/* query panel */}
          <div className="card" style={{ marginBottom: 16 }}>
            <h2>Query</h2>
            <form onSubmit={askRag}>
              <div className="field">
                <label htmlFor="question">Question</label>
                <textarea
                  id="question"
                  rows={3}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Ask a question about your documents..."
                />
              </div>
              <label className="checkbox-row">
                <input
                  type="checkbox"
                  checked={useLlm}
                  onChange={(e) => setUseLlm(e.target.checked)}
                />
                Use local LLM synthesis
              </label>
              <button type="submit" disabled={loading}>
                {loading ? "Asking..." : "Ask RAG"}
              </button>
              {error && <p className="error-msg">{error}</p>}
            </form>
          </div>

          {/* answer panel */}
          <div className="card">
            <h2>Answer</h2>
            {reply ? (
              <pre className="answer-pre">{reply}</pre>
            ) : (
              <p className="answer-placeholder">Answer will appear here.</p>
            )}
          </div>
        </div>

        {/* right column */}
        <div>
          {/* available documents panel */}
          <div className="card" style={{ marginBottom: 16 }}>
            <h2>Available Documents</h2>
            {docLoading ? (
              <span className="loading-dot">Loading...</span>
            ) : documents.length === 0 ? (
              <p className="doc-empty">No documents indexed yet.</p>
            ) : (
              <ul className="doc-list">
                {documents.map((doc) => (
                  <li key={doc.source || doc.name || doc.path}>
                    <span className="doc-name">
                      {doc.source || doc.name || doc.path}
                    </span>
                    <span className="doc-chunks">{doc.chunks} chunk(s)</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* add document panel */}
          <div className="card" style={{ marginBottom: 16 }}>
            <h2>Add Document</h2>
            <form onSubmit={addDocument}>
              <div className="field">
                <label htmlFor="doc-source">Source filename</label>
                <input
                  id="doc-source"
                  type="text"
                  value={newDocSource}
                  onChange={(e) => setNewDocSource(e.target.value)}
                  placeholder="my-note.md"
                />
              </div>
              <div className="field">
                <label htmlFor="doc-text">Document text</label>
                <textarea
                  id="doc-text"
                  rows={4}
                  value={newDocText}
                  onChange={(e) => setNewDocText(e.target.value)}
                  placeholder="Paste or type document content here..."
                />
              </div>
              <div
                style={{
                  display: "flex",
                  gap: 8,
                  alignItems: "center",
                  flexWrap: "wrap",
                }}
              >
                <button type="submit" disabled={indexing}>
                  {indexing ? "Indexing..." : "Index document"}
                </button>
                <button
                  type="button"
                  className="secondary"
                  onClick={reindexDocuments}
                  disabled={docLoading}
                >
                  Reindex all
                </button>
              </div>
              {indexStatus && (
                <p className="status-ok" style={{ marginTop: 6 }}>
                  {indexStatus}
                </p>
              )}
            </form>
          </div>

          {/* recent queries panel */}
          <div className="card">
            <h2>Recent Queries</h2>
            {history.length === 0 ? (
              <p className="doc-empty">No queries yet.</p>
            ) : (
              <ul className="history-list">
                {history.map((item) => (
                  <li key={item.id} className="history-item">
                    <div className="history-meta">
                      <span>{item.timestamp}</span>
                      <span className="history-mode">{item.mode}</span>
                    </div>
                    <div className="history-question">{item.question}</div>
                    <div className="history-preview">{item.preview}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
