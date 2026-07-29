import { Link } from 'react-router-dom';

export default function Hero() {
  return (
    <section className="hero">
      <h1>Intelligent Compliance & Audit Automation at Scale</h1>
      <p>Transform how your enterprise handles policy reviews. Instantly index documents, cross-reference compliance standards, and uncover critical gaps using advanced, grounded AI.</p>
      <div className="hero-buttons">
        <Link to="/audit/new" className="btn-primary" style={{ padding: '14px 32px', fontSize: '16px' }}>Try Now</Link>
        <a href="https://github.com/rupanjali-bharti/Guardian-RAG-Portal" target="_blank" rel="noopener noreferrer" className="btn-secondary">
          <i className="fa-brands fa-github" style={{ marginRight: '8px' }}></i> View Source
        </a>
      </div>
    </section>
  );
}