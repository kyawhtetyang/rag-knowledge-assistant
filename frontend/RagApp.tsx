import React, { useEffect, useMemo, useRef, useState } from 'react';

type Theme = 'light' | 'dark';
type MessageRole = 'assistant' | 'system' | 'user';

type Citation = {
  chunk_index?: number;
  preview?: string;
  score?: number | string;
  source?: string;
};

type ChatMessage = {
  citations?: Citation[];
  id: string;
  role: MessageRole;
  text: string;
};

type AskResponse = {
  answer?: string;
  citations?: Citation[];
  question?: string;
  top_k?: number;
};

type JobStatus = {
  status?: string;
  [key: string]: unknown;
};

type DocumentSummary = {
  document_count?: number;
};

type ClearDemoDataResponse = {
  documents_deleted?: number;
  jobs_deleted?: number;
  status?: string;
};

const API_STORAGE_KEY = 'ragApiBase';
const DEFAULT_THEME: Theme = 'dark';
const normalizeBase = (value: string) => value.trim().replace(/\/$/, '');
const DEFAULT_API_BASE = normalizeBase(import.meta.env.VITE_API_BASE_URL || '');

const createId = () => `${Date.now()}-${Math.random().toString(16).slice(2)}`;

const readStoredTheme = (): Theme => {
  const stored = window.localStorage.getItem('theme');
  return stored === 'light' || stored === 'dark' ? stored : DEFAULT_THEME;
};

const readApiBase = () => window.localStorage.getItem(API_STORAGE_KEY) || DEFAULT_API_BASE;

const formatStatus = (value: unknown) => (typeof value === 'string' ? value : JSON.stringify(value, null, 2));

const RagApp: React.FC = () => {
  const [theme, setTheme] = useState<Theme>(readStoredTheme);
  const [apiBase, setApiBase] = useState(readApiBase);
  const [jobId, setJobId] = useState('');
  const [lastStatus, setLastStatus] = useState<unknown>('Ready.');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [topK, setTopK] = useState(5);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [documentCount, setDocumentCount] = useState<number | null>(null);
  const [clearingDemoData, setClearingDemoData] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const pollTimerRef = useRef<number | null>(null);

  const hasMessages = messages.length > 0;
  const isDark = theme === 'dark';
  const nextTheme = isDark ? 'light' : 'dark';

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    window.localStorage.setItem('theme', theme);
  }, [isDark, theme]);

  useEffect(() => {
    if (!asking && !uploading) {
      inputRef.current?.focus();
    }
  }, [asking, uploading]);

  useEffect(() => {
    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({ block: 'end' });
    });
  }, [messages, asking, uploading]);

  useEffect(() => {
    return () => {
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (showAdvanced) {
      void fetchDocumentSummary();
    }
  }, [showAdvanced, apiBase]);

  const addMessage = (message: Omit<ChatMessage, 'id'>) => {
    setMessages((current) => [...current, { ...message, id: createId() }]);
  };

  const persistApiBase = (value: string) => {
    const normalized = normalizeBase(value);
    setApiBase(normalized);
    if (normalized) {
      window.localStorage.setItem(API_STORAGE_KEY, normalized);
    } else {
      window.localStorage.removeItem(API_STORAGE_KEY);
    }
  };

  const buildUrl = (path: string) => `${apiBase}${path}`;

  const request = async <T,>(path: string, options: RequestInit = {}): Promise<T> => {
    const response = await fetch(buildUrl(path), options);
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error((data as { error?: string }).error || `HTTP ${response.status}`);
    }
    return data as T;
  };

  const fetchDocumentSummary = async () => {
    try {
      const data = await request<DocumentSummary>('/api/documents/summary');
      setDocumentCount(Number(data.document_count || 0));
      return data;
    } catch (error) {
      setLastStatus(`Document count failed: ${(error as Error).message}`);
      return null;
    }
  };

  const clearDemoData = async () => {
    const confirmed = window.confirm('This will remove uploaded documents and citations from this demo. Continue?');
    if (!confirmed) return;

    setClearingDemoData(true);
    try {
      const data = await request<ClearDemoDataResponse>('/api/demo-data', { method: 'DELETE' });
      setDocumentCount(0);
      setJobId('');
      setLastStatus(data);
      addMessage({
        role: 'system',
        text: `Cleared ${data.documents_deleted ?? 0} uploaded document${data.documents_deleted === 1 ? '' : 's'} from this demo.`,
      });
    } catch (error) {
      const message = `Clear failed: ${(error as Error).message}`;
      setLastStatus(message);
      addMessage({ role: 'assistant', text: message });
    } finally {
      setClearingDemoData(false);
    }
  };

  const fetchJob = async (nextJobId: string) => {
    const data = await request<JobStatus>(`/api/jobs/${nextJobId}`);
    setLastStatus(data);

    if (data.status === 'done') {
      void fetchDocumentSummary();
      addMessage({ role: 'system', text: 'Document is ready. Ask a question when you are ready.' });
      if (pollTimerRef.current) {
        window.clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
    }

    return data;
  };

  const startPollingJob = (nextJobId: string) => {
    if (!nextJobId) return;
    if (pollTimerRef.current) {
      window.clearInterval(pollTimerRef.current);
    }
    pollTimerRef.current = window.setInterval(() => {
      fetchJob(nextJobId).catch((error) => {
        setLastStatus(`Job refresh failed: ${(error as Error).message}`);
        if (pollTimerRef.current) {
          window.clearInterval(pollTimerRef.current);
          pollTimerRef.current = null;
        }
      });
    }, 2500);
  };

  const uploadFile = async (file: File) => {
    setUploading(true);
    setLastStatus('Uploading file for async ingestion...');
    addMessage({ role: 'user', text: `Uploaded ${file.name}` });
    addMessage({ role: 'system', text: 'Processing document and building the retrieval index...' });

    try {
      const formData = new FormData();
      formData.append('file', file);
      const data = await request<{ job_id?: number; status?: string }>('/api/ingest-file-async', {
        method: 'POST',
        body: formData,
      });
      const nextJobId = String(data.job_id || '');
      setJobId(nextJobId);
      setLastStatus(data);
      if (data.status === 'done') {
        await fetchDocumentSummary();
        addMessage({ role: 'system', text: 'Document is ready. Ask a question when you are ready.' });
      } else {
        addMessage({ role: 'system', text: `Ingestion job ${nextJobId || 'started'} is running.` });
        startPollingJob(nextJobId);
      }
    } catch (error) {
      setLastStatus(`Upload failed: ${(error as Error).message}`);
      addMessage({ role: 'assistant', text: `Upload failed: ${(error as Error).message}` });
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      void uploadFile(file);
    }
    event.target.value = '';
  };

  const askQuestion = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || asking) return;

    setQuestion('');
    setAsking(true);
    addMessage({ role: 'user', text: trimmedQuestion });

    try {
      const data = await request<AskResponse>('/api/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: trimmedQuestion, top_k: topK }),
      });
      setLastStatus({ question: data.question, top_k: data.top_k, citations: (data.citations || []).length });
      addMessage({
        role: 'assistant',
        text: data.answer || '(empty answer)',
        citations: data.citations || [],
      });
    } catch (error) {
      const message = `Ask failed: ${(error as Error).message}`;
      setLastStatus(message);
      addMessage({ role: 'assistant', text: message });
    } finally {
      setAsking(false);
    }
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void askQuestion();
    }
  };

  const chatMessages = useMemo(
    () =>
      messages.map((message) => (
        <div
          className={`message-row message-row-${message.role}`}
          key={message.id}
        >
          <div className={`message-bubble message-bubble-${message.role}`}>
            <div className="message-text">{message.text}</div>
            {message.role === 'assistant' && message.citations && message.citations.length > 0 && (
              <div className="source-stack">
                <div className="source-label">Sources</div>
                {message.citations.map((citation, index) => (
                  <details className="source-card" key={`${citation.source || 'source'}-${citation.chunk_index ?? index}`}>
                    <summary>
                      <span>{citation.source || 'unknown'}</span>
                      <span>
                        chunk {citation.chunk_index ?? '?'} | score{' '}
                        {typeof citation.score === 'number' ? citation.score.toFixed(4) : citation.score ?? 'n/a'}
                      </span>
                    </summary>
                    <p>{citation.preview || ''}</p>
                  </details>
                ))}
              </div>
            )}
          </div>
        </div>
      )),
    [messages]
  );

  return (
    <>
      <header className="top-toolbar glass">
        <h1>RAG Knowledge Assistant</h1>
        <div className="toolbar-actions">
          <button
            type="button"
            onClick={() => setShowAdvanced((current) => !current)}
            aria-label="Toggle advanced settings"
            title="Advanced settings"
            className="theme-toggle"
          >
            <svg className="theme-icon-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => setTheme(nextTheme)}
            aria-label={`Switch to ${nextTheme} mode`}
            title={`Switch to ${nextTheme} mode`}
            className="theme-toggle"
          >
            {isDark ? (
              <svg className="theme-icon-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v2m0 14v2m9-9h-2M5 12H3m14.95-6.95-1.41 1.41M7.46 16.54l-1.41 1.41m0-11.31 1.41 1.41m10.08 10.08 1.41 1.41M12 7a5 5 0 100 10 5 5 0 000-10z" />
              </svg>
            ) : (
              <svg className="theme-icon-svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12.79A9 9 0 1111.21 3a7 7 0 109.79 9.79z" />
              </svg>
            )}
          </button>
        </div>
      </header>

      {showAdvanced && (
        <aside className="advanced-panel glass">
          <label className="advanced-field">
            <span>Top K</span>
            <input type="number" min="1" max="20" value={topK} onChange={(event) => setTopK(Number(event.target.value || 5))} />
          </label>
          <label className="advanced-field">
            <span>API base</span>
            <input type="text" placeholder="http://127.0.0.1:8010" value={apiBase} onChange={(event) => persistApiBase(event.target.value)} />
          </label>
          <label className="advanced-field">
            <span>Job ID</span>
            <input type="text" value={jobId} onChange={(event) => setJobId(event.target.value)} placeholder="Latest job id" />
          </label>
          <div className="advanced-stat">
            <span>Uploaded documents</span>
            <strong>{documentCount === null ? 'unknown' : documentCount}</strong>
          </div>
          <button
            type="button"
            className="advanced-danger-button"
            onClick={() => {
              void clearDemoData();
            }}
            disabled={clearingDemoData}
          >
            {clearingDemoData ? 'Clearing...' : 'Clear demo documents'}
          </button>
          <pre>{formatStatus(lastStatus)}</pre>
        </aside>
      )}

      <main className={`chat-shell ${hasMessages ? 'chat-shell-active' : 'chat-shell-empty'}`}>
        <section className="chat-window" aria-label="RAG chat">
          <div className="message-stack">
            {!hasMessages && (
              <div className="empty-state">
                <h2>Ask across your documents.</h2>
                <p>Attach a source file, let ingestion finish, then ask a grounded question.</p>
              </div>
            )}
            {chatMessages}
            {asking && (
              <div className="message-row message-row-assistant">
                <div className="message-bubble message-bubble-assistant">
                  <div className="message-text">Running retrieval and answer generation...</div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>
        </section>

        <div className={`composer-wrap ${hasMessages ? 'composer-wrap-bottom' : 'composer-wrap-center'}`}>
          <div className="composer">
            <input ref={fileInputRef} className="file-input" type="file" accept=".txt,.md,.pdf" onChange={handleFileChange} />
            <button
              type="button"
              className="composer-icon-button"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              aria-label="Attach document"
              title="Attach document"
            >
              <svg className="composer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 5V19" strokeLinecap="round" />
                <path d="M5 12H19" strokeLinecap="round" />
              </svg>
            </button>
            <textarea
              ref={inputRef}
              rows={1}
              placeholder={uploading ? 'Ingesting document...' : 'Ask anything'}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              disabled={uploading}
            />
            <button
              type="button"
              className="composer-send-button"
              onClick={() => {
                void askQuestion();
              }}
              disabled={asking || uploading || !question.trim()}
              aria-label="Send message"
              title="Send message"
            >
              <svg className="composer-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M22 2L11 13" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M22 2L15 22L11 13L2 9L22 2Z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>
          <p className="composer-note">
            {uploading ? 'Processing document...' : asking ? 'Thinking...' : 'Answers include citations when retrieval returns sources.'}
          </p>
        </div>
      </main>
    </>
  );
};

export default RagApp;
