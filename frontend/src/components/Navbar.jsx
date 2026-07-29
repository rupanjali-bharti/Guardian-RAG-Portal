import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function Navbar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav>
      <div className="nav-container" style={{ flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
          <Link to="/" className="logo" style={{ textDecoration: 'none', color: 'var(--text-main)' }}>
            <i className="fa-solid fa-shield-halved"></i>
            Guardian RAG
          </Link>
          
          {/* Mobile Toggle Button */}
          <button 
            className="mobile-menu-btn" 
            style={{ margin: 0 }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            <i className={`fa-solid ${isMobileMenuOpen ? 'fa-xmark' : 'fa-bars'}`}></i>
          </button>
        </div>

        {/* Links container - hidden on mobile unless toggled */}
        <div style={{ 
          display: isMobileMenuOpen ? 'flex' : 'none', 
          width: '100%', 
          flexDirection: 'column', 
          gap: '20px', 
          marginTop: '20px' 
        }} className="mobile-nav-content">
          <div className="nav-links" style={{ flexDirection: 'column', gap: '16px' }}>
            <Link to="/" onClick={() => setIsMobileMenuOpen(false)}>Home</Link>
            <a href="/#workflow" onClick={() => setIsMobileMenuOpen(false)}>Workflow</a>
            <a href="/#technology" onClick={() => setIsMobileMenuOpen(false)}>Technology</a>
            <a href="/#security" onClick={() => setIsMobileMenuOpen(false)}>Security & Compliance</a>
          </div>
          <div className="nav-actions" style={{ flexDirection: 'column', width: '100%' }}>
            <a href="#" className="btn-ghost">Log in</a>
            <Link to="/audit/new" className="btn-primary" style={{ width: '100%', textAlign: 'center' }}>Try Now</Link>
          </div>
        </div>

        {/* Desktop Links - hidden on mobile via CSS */}
        <style>{`
          @media (min-width: 901px) {
            .mobile-nav-content { display: none !important; }
            .nav-container > div:first-child { width: auto !important; }
            .nav-container::after { content: ''; display: block; clear: both; }
          }
          @media (max-width: 900px) {
            .nav-container .nav-links, .nav-container .nav-actions { display: none; }
            .mobile-nav-content .nav-links, .mobile-nav-content .nav-actions { display: flex; }
          }
        `}</style>
        
        <div className="nav-links">
          <Link to="/">Home</Link>
          <a href="/#workflow">Workflow</a>
          <a href="/#technology">Technology</a>
          <a href="/#security">Security & Compliance</a>
        </div>
        <div className="nav-actions">
          <a href="#" className="btn-ghost">Log in</a>
          <Link to="/audit/new" className="btn-primary">Try Now</Link>
        </div>
      </div>
    </nav>
  );
}