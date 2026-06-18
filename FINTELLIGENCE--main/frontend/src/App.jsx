import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Archive,
  ArrowRight,
  Bot,
  Download,
  FileText,
  Folder,
  Gauge,
  Grid2X2,
  LogOut,
  Network,
  Search,
  Shield,
  UploadCloud,
  WalletCards,
} from 'lucide-react';
import './App.css';

const TOKEN_KEY = 'fintelligence_token';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', eyebrow: 'COMMAND', title: 'Dashboard', icon: Grid2X2 },
  { id: 'upload', label: 'Upload', eyebrow: 'INGEST', title: 'Upload statement', icon: UploadCloud },
  { id: 'transactions', label: 'Transactions', eyebrow: 'LEDGER', title: 'Transactions', icon: WalletCards },
  { id: 'fraud', label: 'Fraud Analysis', eyebrow: 'SIGNAL', title: 'Fraud Analysis', icon: Shield },
  { id: 'fund-flow', label: 'Fund Flow', eyebrow: 'GRAPH', title: 'Fund Flow', icon: Network },
  { id: 'cases', label: 'Cases', eyebrow: 'DOSSIERS', title: 'Cases', icon: Folder },
  { id: 'ai', label: 'AI Investigator', eyebrow: 'CONVERSATIONAL', title: 'AI Investigator', icon: Bot },
  { id: 'reports', label: 'Reports', eyebrow: 'ARCHIVE', title: 'Reports', icon: FileText },
  { id: 'evidence', label: 'Evidence Locker', eyebrow: 'CHAIN OF CUSTODY', title: 'Evidence Locker', icon: Archive },
];

const detectorEndpoints = [
  ['Large Transaction', '/detect/large-transaction'],
  ['Dormant Account Revival', '/detect/dormant-revival'],
  ['Beneficiary Burst', '/detect/beneficiary-burst'],
  ['High Risk Time', '/detect/high-risk-time'],
  ['Structuring / Smurfing', '/detect/structuring'],
  ['Circular Flow', '/detect/circular-flow'],
];

const formatCurrency = (value) =>
  new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 }).format(Number(value || 0));

const formatDate = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toISOString().slice(0, 10);
};

const severityClass = (value = '') => {
  const normalized = value.toLowerCase();
  if (normalized.includes('critical')) return 'critical';
  if (normalized.includes('high')) return 'high';
  if (normalized.includes('medium')) return 'medium';
  return 'low';
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY) || '');
  const [user, setUser] = useState(null);
  const [activeView, setActiveView] = useState('dashboard');
  const [cases, setCases] = useState([]);
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [caseDetail, setCaseDetail] = useState(null);
  const [overview, setOverview] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [detectors, setDetectors] = useState([]);
  const [graph, setGraph] = useState(null);
  const [evidence, setEvidence] = useState([]);
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState('');

  const api = useCallback(
    async (path, options = {}) => {
      const headers = new Headers(options.headers || {});
      if (!(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
      if (token) headers.set('Authorization', `Bearer ${token}`);

      const response = await fetch(`/api${path}`, { ...options, headers });
      const contentType = response.headers.get('content-type') || '';
      const data = contentType.includes('application/json') ? await response.json() : await response.blob();

      if (!response.ok) {
        const message = data?.error || data?.msg || data?.message || `Request failed: ${response.status}`;
        throw new Error(message);
      }
      return data;
    },
    [token],
  );

  const refreshCases = useCallback(async () => {
    const data = await api('/cases/');
    setCases(data);
    if (!selectedCaseId && data[0]?.id) setSelectedCaseId(data[0].id);
    return data;
  }, [api, selectedCaseId]);

  useEffect(() => {
    if (!token) return;
    api('/auth/me')
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken('');
      });
  }, [api, token]);

  useEffect(() => {
    if (!token) return;
    Promise.allSettled([api('/dashboard/overview'), refreshCases()]).then(([overviewResult]) => {
      if (overviewResult.status === 'fulfilled') setOverview(overviewResult.value);
    });
  }, [api, refreshCases, token]);

  useEffect(() => {
    if (!selectedCaseId || !token) return;
    const loadCaseContext = async () => {
      setLoading(true);
      try {
        const [detail, txns, graphData, evidenceData] = await Promise.all([
          api(`/cases/${selectedCaseId}`),
          api(`/cases/${selectedCaseId}/transactions`),
          api(`/graph/${selectedCaseId}`).catch(() => null),
          api(`/evidence/${selectedCaseId}`).catch(() => []),
        ]);
        setCaseDetail(detail);
        setTransactions(txns);
        setGraph(graphData);
        setEvidence(evidenceData);
      } catch (error) {
        setNotice(error.message);
      } finally {
        setLoading(false);
      }
    };
    loadCaseContext();
  }, [api, selectedCaseId, token]);

  const selectedCase = useMemo(
    () => cases.find((item) => item.id === selectedCaseId) || caseDetail,
    [caseDetail, cases, selectedCaseId],
  );

  const runDetectors = useCallback(async () => {
    if (!selectedCaseId) return;
    setLoading(true);
    setNotice('');
    const results = await Promise.allSettled(
      detectorEndpoints.map(async ([name, path]) => {
        const result = await api(path, {
          method: 'POST',
          body: JSON.stringify({ case_id: selectedCaseId }),
        });
        return normalizeDetector(name, result);
      }),
    );
    setDetectors(
      results.map((result, index) =>
        result.status === 'fulfilled'
          ? result.value
          : { name: detectorEndpoints[index][0], triggered: false, severity: 'low', score: 0, reason: result.reason.message },
      ),
    );
    setLoading(false);
  }, [api, selectedCaseId]);

  if (!token) {
    return <LoginScreen setToken={setToken} />;
  }

  const pageMeta = navItems.find((item) => item.id === activeView) || navItems[0];

  return (
    <div className="app-shell">
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        user={user}
        onLogout={() => {
          localStorage.removeItem(TOKEN_KEY);
          setToken('');
          setUser(null);
        }}
      />
      <main className="workspace">
        <div className="page-topline" />
        <PageHeader
          meta={pageMeta}
          selectedCaseId={selectedCaseId}
          setSelectedCaseId={setSelectedCaseId}
          cases={cases}
        />
        {notice && <div className="notice">{notice}</div>}
        {activeView === 'dashboard' && (
          <Dashboard overview={overview} cases={cases} selectedCase={selectedCase} transactions={transactions} />
        )}
        {activeView === 'upload' && (
          <UploadView
            api={api}
            refreshCases={refreshCases}
            selectedCaseId={selectedCaseId}
            setSelectedCaseId={setSelectedCaseId}
            setNotice={setNotice}
          />
        )}
        {activeView === 'transactions' && <TransactionsView transactions={transactions} selectedCase={selectedCase} />}
        {activeView === 'fraud' && (
          <FraudView detectors={detectors} runDetectors={runDetectors} loading={loading} selectedCaseId={selectedCaseId} />
        )}
        {activeView === 'fund-flow' && <FundFlowView graph={graph} transactions={transactions} />}
        {activeView === 'cases' && (
          <CasesView
            cases={cases}
            selectedCaseId={selectedCaseId}
            setSelectedCaseId={setSelectedCaseId}
            caseDetail={caseDetail}
            detectors={detectors}
            api={api}
          />
        )}
        {activeView === 'ai' && (
          <AiView api={api} selectedCaseId={selectedCaseId} chat={chat} setChat={setChat} transactions={transactions} />
        )}
        {activeView === 'reports' && <ReportsView api={api} selectedCaseId={selectedCaseId} selectedCase={selectedCase} />}
        {activeView === 'evidence' && <EvidenceView evidence={evidence} selectedCase={selectedCase} />}
      </main>
    </div>
  );
}

function LoginScreen({ setToken }) {
  const [email, setEmail] = useState('admin@fintelligence.io');
  const [password, setPassword] = useState('Admin@2026');
  const [error, setError] = useState('');

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.msg || data.error || 'Sign in failed');
      localStorage.setItem(TOKEN_KEY, data.access_token);
      setToken(data.access_token);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-shell">
      <section className="login-art">
        <div className="art-text">
          <span>CASE FILE / 2026 / AML</span>
          <h1>Trace every rupee. Investigate every signal.</h1>
        </div>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <Brand compact />
          <p className="eyebrow">SECURE LOGIN</p>
          <h2>Sign in to your investigation workspace.</h2>
          <p className="muted">Use analyst credentials below, or create users from the backend seed/admin flow.</p>
          <form onSubmit={submit}>
            <label>
              <span>Email</span>
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" />
            </label>
            <label>
              <span>Password</span>
              <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" />
            </label>
            {error && <div className="form-error">{error}</div>}
            <button className="primary-button" type="submit">
              Sign in <ArrowRight size={15} />
            </button>
          </form>
          <div className="demo-line">
            <span>Demo credentials</span>
            <strong>admin@fintelligence.io / Admin@2026</strong>
          </div>
        </div>
      </section>
    </div>
  );
}

function Sidebar({ activeView, setActiveView, user, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <Brand />
      </div>
      <nav>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <button
              className={activeView === item.id ? 'nav-item active' : 'nav-item'}
              key={item.id}
              onClick={() => setActiveView(item.id)}
              type="button"
            >
              <Icon size={17} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
      <div className="signed-in">
        <span>Signed in</span>
        <strong>{user?.name || 'Lead Analyst'}</strong>
        <button onClick={onLogout} type="button">
          <LogOut size={14} /> Sign out
        </button>
      </div>
    </aside>
  );
}

function Brand({ compact = false }) {
  return (
    <div className={compact ? 'brand compact' : 'brand'}>
      <span className="brand-mark">F</span>
      <strong>FINTELLIGENCE</strong>
      {!compact && <small>FORENSIC INTEL / V1.0</small>}
    </div>
  );
}

function PageHeader({ meta, selectedCaseId, setSelectedCaseId, cases }) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{meta.eyebrow}</p>
        <h1>{meta.title}</h1>
      </div>
      {cases.length > 0 && !['dashboard', 'upload'].includes(meta.id) && (
        <select value={selectedCaseId} onChange={(event) => setSelectedCaseId(event.target.value)}>
          {cases.map((item) => (
            <option key={item.id} value={item.id}>
              {item.title || `Investigation ${item.id.slice(0, 8)}`}
            </option>
          ))}
        </select>
      )}
    </header>
  );
}

function Dashboard({ overview, cases, selectedCase, transactions }) {
  const metrics = [
    ['Statements', overview?.total_statements || 0],
    ['Transactions', overview?.total_transactions || transactions.length],
    ['High risk cases', overview?.high_risk_cases || 0],
    ['AML alerts', overview?.aml_alerts || 0],
  ];

  return (
    <section className="stack">
      <div className="metric-grid">
        {metrics.map(([label, value]) => (
          <div className="metric" key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <div className="split">
        <div className="panel">
          <PanelTitle icon={Gauge} title="Active investigations" />
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => (
                <tr key={item.id}>
                  <td>{item.title}</td>
                  <td><Badge value={item.severity} /></td>
                  <td>{item.status}</td>
                  <td>{formatDate(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <PanelTitle icon={Shield} title="Current case signal" />
          <div className="case-snapshot">
            <span>{selectedCase?.id?.slice(0, 8) || 'No case'}</span>
            <strong>{selectedCase?.title || 'Upload a statement to begin'}</strong>
            <p>{selectedCase?.description || 'The workspace will populate with detector results, transactions, fund flow, reports, and evidence once data is available.'}</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function UploadView({ api, refreshCases, selectedCaseId, setSelectedCaseId, setNotice }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [caseTitle, setCaseTitle] = useState('Statement investigation');
  const [busy, setBusy] = useState(false);

  const upload = async () => {
    if (!file) {
      setNotice('Choose a PDF, CSV, spreadsheet, or image before analyzing.');
      return;
    }
    setBusy(true);
    setNotice('');
    try {
      let caseId = selectedCaseId;
      if (!caseId) {
        const created = await api('/cases/', {
          method: 'POST',
          body: JSON.stringify({ title: caseTitle, description: 'Uploaded from forensic intake workspace.', severity: 'medium' }),
        });
        caseId = created.id;
        setSelectedCaseId(caseId);
      }
      const form = new FormData();
      form.append('case_id', caseId);
      form.append('file', file);
      const result = await api('/upload/', { method: 'POST', body: form });
      await refreshCases();
      setNotice(`Statement analyzed: ${result.transactions_count} transactions from ${result.bank_detected || 'uploaded file'}.`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="upload-view">
      <p className="subcopy">PDF, CSV or Excel. We normalize into the canonical schema and run the detector suite automatically.</p>
      <label className="case-title">
        <span>Case title for new uploads</span>
        <input value={caseTitle} onChange={(event) => setCaseTitle(event.target.value)} />
      </label>
      <button className="dropzone" type="button" onClick={() => inputRef.current?.click()}>
        <UploadCloud size={38} />
        <strong>{file ? file.name : 'Drop a statement here, or click to browse'}</strong>
        <span>PDF / CSV / XLSX / JPG / PNG</span>
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.csv,.xls,.xlsx,.png,.jpg,.jpeg"
        hidden
        onChange={(event) => setFile(event.target.files?.[0] || null)}
      />
      <div className="upload-actions">
        <button className="primary-button" onClick={upload} disabled={busy} type="button">
          {busy ? 'Analyzing statement' : 'Analyze statement'}
        </button>
        <span><FileText size={15} /> PDF</span>
        <span><FileText size={15} /> Spreadsheet</span>
        <span><FileText size={15} /> Image / scan</span>
      </div>
    </section>
  );
}

function TransactionsView({ transactions, selectedCase }) {
  const [query, setQuery] = useState('');
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const filtered = transactions.filter((txn) => {
    const text = `${txn.description || ''} ${txn.sender_account || ''} ${txn.receiver_account || ''}`.toLowerCase();
    return text.includes(query.toLowerCase()) && (!flaggedOnly || txn.is_flagged || txn.risk_level !== 'low');
  });

  return (
    <section className="stack">
      <div className="toolbar">
        <div className="select-like">{selectedCase?.title || 'No case selected'} / {(selectedCase?.risk_level || 'open').toUpperCase()}</div>
        <label className="search-box">
          <Search size={16} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search description / counterparty" />
        </label>
        <label className="check-label">
          <input checked={flaggedOnly} onChange={(event) => setFlaggedOnly(event.target.checked)} type="checkbox" />
          Flagged only
        </label>
        <span className="row-count">{filtered.length} rows</span>
      </div>
      <div className="table-frame">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Description</th>
              <th>Sender - Receiver</th>
              <th>Amount</th>
              <th>Dr/Cr</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((txn) => (
              <tr key={txn.id}>
                <td>{formatDate(txn.date)}</td>
                <td className="truncate">{txn.description || '-'}</td>
                <td>{txn.sender_account || 'SELF'} - {txn.receiver_account || 'UNKNOWN'}</td>
                <td>{formatCurrency(txn.amount)}</td>
                <td>{txn.type}</td>
                <td><Badge value={txn.risk_level || (txn.is_flagged ? 'flagged' : 'clear')} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function FraudView({ detectors, runDetectors, loading, selectedCaseId }) {
  const triggered = detectors.filter((item) => item.triggered || item.score > 0);
  const passed = detectors.filter((item) => !triggered.includes(item));

  return (
    <section className="stack">
      <div className="toolbar right">
        <button className="primary-button" onClick={runDetectors} disabled={!selectedCaseId || loading} type="button">
          {loading ? 'Running detectors' : 'Run detector suite'}
        </button>
      </div>
      <div className="detector-grid">
        <div>
          <p className="eyebrow">TRIGGERED / {triggered.length}</p>
          {triggered.map((item) => <DetectorCard item={item} key={item.name} />)}
        </div>
        <div>
          <p className="eyebrow">PASSED / {passed.length}</p>
          {passed.map((item) => (
            <div className="passed-card" key={item.name}>
              <span>{item.name}</span>
              <strong>Clear</strong>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DetectorCard({ item }) {
  return (
    <article className="detector-card">
      <div>
        <strong>{item.name}</strong>
        <p>{item.reason || 'Potential suspicious activity detected.'}</p>
      </div>
      <div className="score-stack">
        <Badge value={item.severity || 'medium'} />
        <span>Score {Math.round(item.score || 0)}</span>
      </div>
    </article>
  );
}

function FundFlowView({ graph, transactions }) {
  const nodes = graph?.nodes || [];
  const links = graph?.links || [];
  const fallbackNodes = nodes.length
    ? nodes
    : Array.from(new Set(transactions.flatMap((txn) => [txn.sender_account || 'SELF', txn.receiver_account || 'UNKNOWN']))).map((id) => ({ id }));

  return (
    <section className="stack">
      <div className="metric-grid three">
        <div className="metric"><span>Hubs</span><strong>{fallbackNodes.length ? fallbackNodes[0].id || fallbackNodes[0].label : '-'}</strong></div>
        <div className="metric"><span>Sinks</span><strong>{fallbackNodes.length ? fallbackNodes.at(-1).id || fallbackNodes.at(-1).label : '-'}</strong></div>
        <div className="metric"><span>Paths</span><strong>{links.length || transactions.length}</strong></div>
      </div>
      <div className="flow-canvas">
        {fallbackNodes.slice(0, 7).map((node, index) => (
          <div className={`flow-node n${index}`} key={node.id || node.label}>
            <strong>{node.id || node.label}</strong>
            <span>PARTY</span>
          </div>
        ))}
        {fallbackNodes.length === 0 && <span className="empty-line">Upload or select a case to reconstruct fund flow.</span>}
      </div>
      <div className="panel compact-panel">
        <p className="eyebrow">CIRCULAR PATHS</p>
        <strong>{links.length ? `${links.length} graph relationship(s) found` : 'SELF - UNKNOWN'}</strong>
      </div>
    </section>
  );
}

function CasesView({ cases, selectedCaseId, setSelectedCaseId, caseDetail, detectors, api }) {
  const [note, setNote] = useState('');
  const [message, setMessage] = useState('');

  const addNote = async () => {
    if (!note.trim() || !selectedCaseId) return;
    await api(`/evidence/${selectedCaseId}/upload`, {
      method: 'POST',
      body: (() => {
        const form = new FormData();
        form.append('item_type', 'note');
        form.append('note_text', note);
        return form;
      })(),
    });
    setNote('');
    setMessage('Investigator note added to evidence locker.');
  };

  return (
    <section className="stack">
      <div className="table-frame">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Severity</th>
              <th>Suspicion</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr
                className={item.id === selectedCaseId ? 'selected-row' : ''}
                key={item.id}
                onClick={() => setSelectedCaseId(item.id)}
              >
                <td>Investigation: {item.id.slice(0, 8)}</td>
                <td><Badge value={item.severity} /></td>
                <td>{item.suspicion_score || caseDetail?.suspicion_score || '-'}</td>
                <td>{item.status}</td>
                <td>{formatDate(item.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {caseDetail && (
        <div className="panel">
          <div className="case-detail-head">
            <div>
              <p className="eyebrow">CASE / {caseDetail.id.slice(0, 8)}</p>
              <h2>Investigation: {caseDetail.id.slice(0, 8)}</h2>
              <p>{caseDetail.statements?.[0]?.filename || 'No statement attached yet'}</p>
            </div>
            <Badge value={caseDetail.severity} />
          </div>
          <div className="metric-grid four">
            <div className="metric"><span>Suspicion</span><strong>{caseDetail.suspicion_score || 0}</strong></div>
            <div className="metric"><span>Risk</span><strong>{caseDetail.risk_level || 'low'}</strong></div>
            <div className="metric"><span>Statements</span><strong>{caseDetail.statements?.length || 0}</strong></div>
            <div className="metric"><span>Triggered</span><strong>{detectors.filter((item) => item.triggered).length}</strong></div>
          </div>
          <p className="summary-copy">
            This investigation workspace consolidates statement evidence, transaction patterns, detector output, and fund-flow context for analyst review.
          </p>
        </div>
      )}
      <div className="panel">
        <PanelTitle icon={FileText} title="Investigator notes" />
        <div className="note-row">
          <input value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add a note..." />
          <button className="dark-button" onClick={addNote} type="button">Add</button>
        </div>
        {message && <p className="muted">{message}</p>}
      </div>
    </section>
  );
}

function AiView({ api, selectedCaseId, chat, setChat, transactions }) {
  const [question, setQuestion] = useState('');
  const presets = [
    'Show suspicious transactions',
    'Why was this case flagged?',
    'Trace the money trail',
    'Explain this case in plain language',
  ];

  const ask = async (text = question) => {
    if (!text.trim() || !selectedCaseId) return;
    const next = [...chat, { role: 'user', content: text }];
    setChat(next);
    setQuestion('');
    try {
      const answer = await api('/ai/chat', {
        method: 'POST',
        body: JSON.stringify({ case_id: selectedCaseId, question: text, conversation_history: next }),
      });
      setChat([...next, { role: 'assistant', content: answer.answer || answer.response || JSON.stringify(answer) }]);
    } catch (error) {
      const fallback = transactions.length
        ? `I found ${transactions.length} transaction(s) in this case. Review high-value credits/debits and run the detector suite for a stronger explanation.`
        : error.message;
      setChat([...next, { role: 'assistant', content: fallback }]);
    }
  };

  return (
    <section className="ai-view">
      <p className="subcopy">Powered by the backend investigator endpoint. Ask around the selected statement context.</p>
      <div className="preset-row">
        {presets.map((preset) => (
          <button key={preset} onClick={() => ask(preset)} type="button">{preset}</button>
        ))}
      </div>
      <div className="chat-window">
        {chat.length === 0 ? (
          <span className="empty-line">// Empty session. Type a question below or pick a preset.</span>
        ) : (
          chat.map((item, index) => (
            <div className={`chat-line ${item.role}`} key={`${item.role}-${index}`}>
              <strong>{item.role}</strong>
              <p>{item.content}</p>
            </div>
          ))
        )}
      </div>
      <form className="chat-form" onSubmit={(event) => { event.preventDefault(); ask(); }}>
        <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about this case..." />
        <button className="dark-button" type="submit">Send</button>
      </form>
    </section>
  );
}

function ReportsView({ api, selectedCaseId, selectedCase }) {
  const [busy, setBusy] = useState(false);
  const download = async () => {
    if (!selectedCaseId) return;
    setBusy(true);
    try {
      const blob = await api(`/reports/generate/${selectedCaseId}`, { headers: {} });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `FINTELLIGENCE_Report_${selectedCaseId.slice(0, 8)}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="stack">
      <p className="subcopy">Generated PDF investigation packets: case summary, detector results, money trail, notes.</p>
      <div className="table-frame">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>Case</th>
              <th>Size</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><FileText size={15} /> FINTELLIGENCE_Report_{selectedCaseId?.slice(0, 8) || 'case'}.pdf</td>
              <td>{selectedCase?.id?.slice(0, 8) || '-'}</td>
              <td>Generated</td>
              <td>
                <button className="link-button" onClick={download} disabled={!selectedCaseId || busy} type="button">
                  <Download size={14} /> {busy ? 'Preparing' : 'Download'}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}

function EvidenceView({ evidence, selectedCase }) {
  const synthetic = selectedCase?.statements?.map((statement) => ({
    id: statement.id,
    item_type: 'statement',
    file_path: statement.filename,
    created_at: null,
  })) || [];
  const items = evidence.length ? evidence : synthetic;

  return (
    <section className="locker-grid">
      {items.map((item) => (
        <article className="locker-card" key={item.id}>
          <FileText size={24} />
          <span>{(item.item_type || 'evidence').toUpperCase()}</span>
          <strong>{item.file_path?.split(/[\\/]/).pop() || item.note_text || 'Evidence note'}</strong>
          <small>{formatDate(item.created_at)}</small>
        </article>
      ))}
      {items.length === 0 && <p className="empty-line">No evidence has been stored for this case yet.</p>}
    </section>
  );
}

function PanelTitle({ icon: Icon, title }) {
  return (
    <div className="panel-title">
      <Icon size={16} />
      <span>{title}</span>
    </div>
  );
}

function Badge({ value }) {
  return <span className={`badge ${severityClass(value)}`}>{value || 'clear'}</span>;
}

function normalizeDetector(name, result) {
  const item = Array.isArray(result) ? result[0] : result;
  const triggered = Boolean(item?.triggered || item?.is_triggered || item?.matches?.length || item?.transactions?.length);
  return {
    name,
    triggered,
    score: item?.score || item?.risk_score || (triggered ? 50 : 0),
    severity: item?.severity || item?.risk_level || (triggered ? 'high' : 'low'),
    reason: item?.reason || item?.message || item?.description || (triggered ? 'Detector returned suspicious matches.' : 'No suspicious signal returned.'),
  };
}

export default App;
