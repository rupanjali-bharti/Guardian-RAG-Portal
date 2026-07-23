import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';

const API_BASE_URL = 'http://127.0.0.1:5001';

function getFileIcon(fileName = '') {
  const lowerName = fileName.toLowerCase();
  if (lowerName.endsWith('.pdf')) return 'fa-regular fa-file-pdf';
  if (lowerName.endsWith('.json')) return 'fa-solid fa-file-code';
  return 'fa-solid fa-file-lines';
}

export default function Audit() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [files, setFiles] = useState([]);
  const [summary, setSummary] = useState({
    total_items: 0,
    verified_count: 0,
    partial_count: 0,
    significant_count: 0,
    critical_count: 0,
    gaps_found: 0,
    compliance_score: 0,
  });
  const [results, setResults] = useState([]);
  const [error, setError] = useState('');

  const loadAuditData = async () => {
    try {
      setError('');
      const response = await fetch(`${API_BASE_URL}/api/audit`);
      if (!response.ok) {
        throw new Error('Unable to reach the backend audit service.');
      }
      const data = await response.json();
      setFiles((data.documents || []).map((file, index) => ({
        id: index + 1,
        name: file.name,
        size: file.size,
        icon: getFileIcon(file.name),
      })));
      setSummary(data.summary || summary);
      setResults(data.results || []);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Could not load audit data from the backend.');
    }
  };

  useEffect(() => {
    loadAuditData();
  }, []);

  const removeFile = (id) => {
    setFiles(files.filter(file => file.id !== id));
  };

  const handleGenerateIndex = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/rag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questions: results.map((item) => item.Question) }),
      });
      if (!response.ok) {
        throw new Error('RAG generation failed.');
      }
      const data = await response.json();
      setResults(data.results || []);
      setSummary((currentSummary) => ({
        ...currentSummary,
        total_items: data.results?.length || currentSummary.total_items,
        verified_count: data.results?.filter((item) => item.Status === 'Verified').length || currentSummary.verified_count,
        partial_count: data.results?.filter((item) => item.Status === 'Partial Info').length || currentSummary.partial_count,
        significant_count: data.results?.filter((item) => item.Status === 'Significant Gap').length || currentSummary.significant_count,
        critical_count: data.results?.filter((item) => item.Status === 'Critical Gap').length || currentSummary.critical_count,
        gaps_found: data.results?.filter((item) => item.Status !== 'Verified').length || currentSummary.gaps_found,
        compliance_score: data.results?.length
          ? Math.round((data.results.filter((item) => item.Status === 'Verified').length / data.results.length) * 100)
          : currentSummary.compliance_score,
      }));
    } catch (err) {
      console.error(err);
      setError(err.message || 'Could not regenerate the audit data.');
    } finally {
      setIsGenerating(false);
    }
  };

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
        
        {/* Mobile Overlay (clicks outside sidebar close it) */}
        <div 
          className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`}
          onClick={() => setIsSidebarOpen(false)}
        ></div>

        {/* Sidebar Component */}
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
            <button className="add-doc-btn" title="Add Document">
              <i className="fa-solid fa-plus"></i>
            </button>
          </div>

          <div className="file-list">
            {files.length > 0 ? (
              files.map(file => (
                <div className="file-item" key={file.id}>
                  <div className="file-details">
                    <i className={file.icon}></i>
                    <div>
                      <div className="file-name">{file.name}</div>
                      <div className="file-size">{file.size}</div>
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
              /* EMPTY STATE */
              <div className="empty-state">
                <i className="fa-regular fa-folder-open"></i>
                <p>No documents found</p>
                <small>Upload files to build your graph index.</small>
              </div>
            )}
          </div>

          <button 
            className="btn-primary full-width" 
            onClick={handleGenerateIndex}
            disabled={isGenerating || files.length === 0}
            style={{ opacity: (isGenerating || files.length === 0) ? 0.7 : 1, cursor: (isGenerating || files.length === 0) ? 'not-allowed' : 'pointer' }}
          >
            {isGenerating ? (
              <><i className="fa-solid fa-spinner"></i> Generating Index...</>
            ) : (
              <><i className="fa-solid fa-network-wired"></i> Generate Graph Index</>
            )}
          </button>
        </aside>

        {/* Main Content Component */}
        <main className="main-content">
          <div className="top-nav">
            <div className="page-title">
              <button 
                className="mobile-menu-btn" 
                onClick={() => setIsSidebarOpen(true)}
              >
                <i className="fa-solid fa-bars"></i>
              </button>
              <i className="fa-solid fa-chart-pie" style={{ display: window.innerWidth > 900 ? 'block' : 'none' }}></i>
              <h1>Executive Audit Dashboard</h1>
            </div>
            <div className="top-actions">
              <button className="btn-outline">
                <i className="fa-solid fa-download" style={{ marginRight: '6px' }}></i> 
                <span>Export Report</span>
              </button>
              <button className="btn-outline" title="Settings">
                <i className="fa-solid fa-gear"></i>
              </button>
            </div>
          </div>

          {/* Metrics Header */}
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

          {/* Progress Bar */}
          <div className="progress-container">
            <div className="progress-bar"></div>
          </div>

          {/* Status Breakdown Cards */}
          <div className="status-cards">
            {statusCards.map((card) => (
              <div className={`status-card ${card.variant}`} key={card.label}>
                <div className="status-number">{card.value}</div>
                <div className="status-label">{card.label}</div>
              </div>
            ))}
          </div>

          {/* Detailed Item Review */}
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
                  <div className={item.Status === 'Verified' ? 'badge-verified' : 'badge-partial'}>
                    <i className={item.Status === 'Verified' ? 'fa-solid fa-check' : 'fa-solid fa-circle-exclamation'}></i> {item.Status}
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