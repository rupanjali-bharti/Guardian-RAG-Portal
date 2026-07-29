import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { API_ENDPOINT } from '../utils/api';


function getFileIcon(fileName = '') {
  const lowerName = fileName.toLowerCase();
  if (lowerName.endsWith('.pdf')) return 'fa-regular fa-file-pdf';
  if (lowerName.endsWith('.json')) return 'fa-solid fa-file-code';
  return 'fa-solid fa-file-lines';
}

function formatBytes(size = 0) {
  if (!size) return '0 KB';
  const units = ['B', 'KB', 'MB', 'GB'];
  const idx = Math.min(Math.floor(Math.log(size) / Math.log(1024)), units.length - 1);
  return `${(size / 1024 ** idx).toFixed(idx === 0 ? 0 : 1)} ${units[idx]}`;
}

function buildSummary(results = []) {
  const totalItems = results.length;
  const verifiedCount = results.filter((item) => item.Status === 'Verified').length;
  const partialCount = results.filter((item) => item.Status === 'Partial Info').length;
  const significantCount = results.filter((item) => item.Status === 'Significant Gap').length;
  const criticalCount = results.filter((item) => item.Status === 'Critical Gap').length;
  const gapsFound = totalItems - verifiedCount;
  const complianceScore = totalItems ? Math.round((verifiedCount / totalItems) * 100) : 0;

  return {
    total_items: totalItems,
    verified_count: verifiedCount,
    partial_count: partialCount,
    significant_count: significantCount,
    critical_count: criticalCount,
    gaps_found: gapsFound,
    compliance_score: complianceScore,
  };
}

export default function Audit() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [activeView, setActiveView] = useState('existing');
  const [demoFiles, setDemoFiles] = useState([]);
  const [sessionFiles, setSessionFiles] = useState([]);
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');
  const [policyFiles, setPolicyFiles] = useState([]);
  const [questionnaireFile, setQuestionnaireFile] = useState(null);
  const [draggingPolicies, setDraggingPolicies] = useState(false);
  const [draggingQuestionnaire, setDraggingQuestionnaire] = useState(false);
  const policyInputRef = useRef(null);
  const questionnaireInputRef = useRef(null);

  const summary = useMemo(() => buildSummary(results), [results]);

  const loadAuditData = async () => {
    try {
      setError('');
      const response = await fetch(API_ENDPOINT('audit'));
      if (!response.ok) {
        throw new Error('Unable to reach the backend audit service.');
      }
      const data = await response.json();
      setDemoFiles((data.documents || []).map((file, index) => ({
        id: `demo-${index + 1}`,
        name: file.name,
        size: file.size || formatBytes(file.sizeBytes || 0),
        icon: getFileIcon(file.name),
        score: file.audit_score,
      })));
      setSessionFiles([]);
      setResults(data.results || []);
      setPolicyFiles([]);
      setQuestionnaireFile(null);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Could not load audit data from the backend.');
    }
  };

  useEffect(() => {
    loadAuditData();
  }, []);

  const removeFile = (id) => {
    if (activeView === 'existing') {
      setDemoFiles((currentFiles) => currentFiles.filter((file) => file.id !== id));
    } else {
      setSessionFiles((currentFiles) => currentFiles.filter((file) => file.id !== id));
    }
  };

  const handlePoliciesSelect = (selectedFiles) => {
    const validFiles = Array.from(selectedFiles || []).filter((file) => file.name.toLowerCase().endsWith('.txt'));
    if (validFiles.length === 0) {
      setError('Please upload .txt policy files.');
      return;
    }

    setError('');
    const newEntries = validFiles.map((file, index) => ({
      id: `upload-${Date.now()}-${index}`,
      name: file.name,
      size: formatBytes(file.size),
      icon: getFileIcon(file.name),
      score: null,
      file,
    }));

    setSessionFiles((currentFiles) => [...currentFiles.filter((file) => !file.file), ...newEntries]);
    setPolicyFiles((currentFiles) => [...currentFiles, ...validFiles]);
  };

  const handleStartAuditRun = async (event) => {
    event.preventDefault();
    if (!questionnaireFile) {
      setError('Please upload a questionnaire CSV before starting the audit run.');
      return;
    }

    setIsGenerating(true);
    setError('');

    try {
      const formData = new FormData();
      policyFiles.forEach((file) => formData.append('policy_files', file));
      formData.append('questionnaire_file', questionnaireFile);

      const response = await fetch(API_ENDPOINT('audit'), {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Unable to start the audit run.');
      }

      const data = await response.json();
      setSessionFiles((data.documents || []).map((file, index) => ({
        id: `session-${index + 1}`,
        name: file.name,
        size: file.size || formatBytes(file.sizeBytes || 0),
        icon: getFileIcon(file.name),
        score: file.audit_score,
      })));
      setResults(data.results || []);
      setActiveView('new');
    } catch (err) {
      console.error(err);
      setError(err.message || 'Could not run the audit workflow.');
    } finally {
      setIsGenerating(false);
    }
  };

  const visibleFiles = [...demoFiles];
  if (questionnaireFile) {
    visibleFiles.push({
      id: 'questionnaire-file',
      name: questionnaireFile.name,
      size: formatBytes(questionnaireFile.size),
      icon: 'fa-solid fa-file-csv',
      score: null,
      file: questionnaireFile,
    });
  }

  const statusCards = useMemo(() => [
    { label: 'Verified', value: summary.verified_count, variant: 'verified' },
    { label: 'Partial Info', value: summary.partial_count, variant: 'partial' },
    { label: 'Significant Gap', value: summary.significant_count, variant: 'significant' },
    { label: 'Critical Gap', value: summary.critical_count, variant: 'critical' },
  ], [summary]);

  return (
    <>
      <Navbar />

      <div className="audit-layout" style={{ paddingTop: '73px' }}>
        <div
          className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`}
          onClick={() => setIsSidebarOpen(false)}
        ></div>

        <aside className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
          <div className="brand">
            <div className="brand-logo">
              <i className="fa-solid fa-shield-halved"></i>
              <h2>Guardian RAG</h2>
            </div>
            <Link to="/" className="back-link" title="Exit to Website">
              <i className="fa-solid fa-arrow-right-from-bracket"></i>
            </Link>
          </div>

          <div className="user-info">
            <div className="user-avatar">R</div>
            <div>
              User: <span>Rupanjali</span><br />
              <small style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Admin Access</small>
            </div>
          </div>

          <div className="sidebar-section-title">
            <span>Knowledge Base</span>
          </div>

          <div className="view-switcher">
            <button className={`view-chip active`}>
              Existing Audits
            </button>
          </div>

          <div className="file-list">
            {visibleFiles.length > 0 ? (
              visibleFiles.map((file) => (
                <div className="file-item" key={file.id}>
                  <div className="file-details">
                    <i className={file.icon}></i>
                    <div>
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{file.size}</div>
                      {file.score !== null && file.score !== undefined ? (
                        <div className="file-score">Score: {file.score}%</div>
                      ) : null}
                    </div>
                  </div>
                  <i
                    className="fa-solid fa-trash-can file-remove"
                    onClick={() => removeFile(file.id)}
                    title="Remove file"
                  ></i>
                </div>
              ))
            ) : (
              <div className="empty-state">
                <i className="fa-regular fa-folder-open"></i>
                <p>{activeView === 'existing' ? 'No existing documents' : 'No new audit documents'}</p>
                <small>{activeView === 'existing' ? 'Use the demo baseline to review the default audit set.' : 'Upload policy files to begin a new audit session.'}</small>
              </div>
            )}
          </div>

          {activeView === 'new' ? (
            <div
              className={`upload-zone ${draggingPolicies ? 'dragging' : ''}`}
              onDragOver={(event) => {
                event.preventDefault();
                setDraggingPolicies(true);
              }}
              onDragLeave={() => setDraggingPolicies(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDraggingPolicies(false);
                handlePoliciesSelect(event.dataTransfer.files);
              }}
            >
              <i className="fa-solid fa-cloud-arrow-up"></i>
              <strong>Upload Policies (.txt)</strong>
              <span>Drag and drop policy files here</span>
              <button type="button" className="btn-outline small" onClick={() => policyInputRef.current?.click()}>
                Choose Files
              </button>
              <input
                ref={policyInputRef}
                type="file"
                accept=".txt"
                multiple
                hidden
                onChange={(event) => handlePoliciesSelect(event.target.files)}
              />
            </div>
          ) : null}
        </aside>

        <main className="main-content">
          <div className="top-nav">
            <div className="page-title">
              <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(true)}>
                <i className="fa-solid fa-bars"></i>
              </button>
              <i className="fa-solid fa-chart-pie" style={{ display: typeof window !== 'undefined' && window.innerWidth > 900 ? 'block' : 'none' }}></i>
              <h1>Executive Audit Dashboard</h1>
            </div>
            <div className="top-actions">
              <Link to="/audit" className="btn-primary" style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', marginRight: '10px' }}>
                <i className="fa-solid fa-plus" style={{ marginRight: '6px' }}></i>
                <span>New Audit</span>
              </Link>
              <button className="btn-outline" onClick={() => loadAuditData()}>
                <i className="fa-solid fa-rotate-right" style={{ marginRight: '6px' }}></i>
                <span>Reload Demo</span>
              </button>
            </div>
          </div>

          {error ? (
            <div className="review-card" style={{ marginBottom: '16px', borderColor: '#ff6b6b' }}>
              <strong>Connection issue:</strong> {error}
            </div>
          ) : null}

          <div className="metrics-grid">
            <div className="metric-group">
              <div className="metric-label">Compliance Score</div>
              <div className="metric-value">{summary.compliance_score}%</div>
            </div>
            <div className="metric-group">
              <div className="metric-label">Total Scope</div>
              <div className="metric-value">
                {summary.total_items} <span style={{ fontSize: '16px', color: 'var(--text-muted)' }}>Items</span>
              </div>
            </div>
            <div className="metric-group">
              <div className="metric-label">Verified Controls</div>
              <div className="metric-value">{summary.verified_count}</div>
            </div>
            <div className="metric-group">
              <div className="metric-label">Gaps Found</div>
              <div className="metric-value">{summary.gaps_found}</div>
              <div className="metric-trend">
                <i className="fa-solid fa-arrow-trend-down"></i> {summary.gaps_found}
              </div>
            </div>
          </div>

          <div className="progress-container">
            <div className="progress-bar" style={{ width: `${summary.compliance_score}%` }}></div>
          </div>

          <div className="status-cards">
            {statusCards.map((card) => (
              <div className={`status-card ${card.variant}`} key={card.label}>
                <div className="status-number">{card.value}</div>
                <div className="status-label">{card.label}</div>
              </div>
            ))}
          </div>

          {activeView === 'new' ? (
            <div className="upload-card">
              <div className="upload-card-header">
                <h3>Run a New Audit Session</h3>
                <p>Upload your questionnaire CSV and any policy documents to generate a fresh audit view.</p>
              </div>

              <form onSubmit={handleStartAuditRun} className="upload-form">
                <div
                  className={`upload-zone questionnaire ${draggingQuestionnaire ? 'dragging' : ''}`}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDraggingQuestionnaire(true);
                  }}
                  onDragLeave={() => setDraggingQuestionnaire(false)}
                  onDrop={(event) => {
                    event.preventDefault();
                    setDraggingQuestionnaire(false);
                    const droppedFile = event.dataTransfer.files?.[0];
                    if (droppedFile?.name.toLowerCase().endsWith('.csv')) {
                      setQuestionnaireFile(droppedFile);
                    } else {
                      setError('Please upload a .csv questionnaire file.');
                    }
                  }}
                >
                  <i className="fa-solid fa-file-csv"></i>
                  <strong>Upload Questionnaire (.csv)</strong>
                  <span>{questionnaireFile ? questionnaireFile.name : 'Drag and drop your questionnaire CSV here'}</span>
                  <button type="button" className="btn-outline small" onClick={() => questionnaireInputRef.current?.click()}>
                    Choose File
                  </button>
                  <input
                    ref={questionnaireInputRef}
                    type="file"
                    accept=".csv"
                    hidden
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      if (file?.name.toLowerCase().endsWith('.csv')) {
                        setQuestionnaireFile(file);
                      } else {
                        setError('Please upload a .csv questionnaire file.');
                      }
                    }}
                  />
                </div>

                <button type="submit" className="btn-primary full-width" disabled={isGenerating || !questionnaireFile}>
                  {isGenerating ? (
                    <><i className="fa-solid fa-spinner"></i> Running Audit...</>
                  ) : (
                    <><i className="fa-solid fa-play"></i> Start Audit Run</>
                  )}
                </button>
              </form>
            </div>
          ) : null}

          <h3 className="section-title">
            <i className="fa-solid fa-list-check"></i> Active Item Reviews
          </h3>

          {results.length > 0 ? results.map((item, index) => (
            <div className="review-card" key={`${item.Question}-${index}`} style={{ marginBottom: '16px' }}>
              <div className="review-header">
                <div className="review-question">
                  <span>ITEM {index + 1}:</span> {item.Question}
                </div>
                <div className="review-meta">
                  <span className="gap-text">Gap: {item.GapPercentage ?? 0}%</span>
                  <div className={
                    item.Status === 'Verified'
                      ? 'badge-verified'
                      : item.Status === 'Partial Info'
                        ? 'badge-partial'
                        : item.Status === 'Significant Gap'
                          ? 'badge-significant'
                          : 'badge-critical'
                  }>
                    <i className={
                      item.Status === 'Verified'
                        ? 'fa-solid fa-check'
                        : item.Status === 'Critical Gap'
                          ? 'fa-solid fa-triangle-exclamation'
                          : 'fa-solid fa-circle-exclamation'
                    }></i> {item.Status}
                  </div>
                </div>
              </div>

              <div className="response-section">
                <h4>AI Auditor Response</h4>
                <div className="response-block">
                  <i
                    className="fa-regular fa-copy copy-icon"
                    title="Copy to clipboard"
                    onClick={() => navigator.clipboard?.writeText(item.Answer)}
                  ></i>
                  {item.Answer}
                </div>
                <div className="source-text">
                  <i className="fa-solid fa-book-bookmark"></i>
                  <strong>Sources:</strong> {item.Citation || 'No sources available'}
                </div>
              </div>
            </div>
          )) : (
            <div className="review-card">No audit results available yet. Run the backend audit flow to populate the review.</div>
          )}
        </main>
      </div>
    </>
  );
}