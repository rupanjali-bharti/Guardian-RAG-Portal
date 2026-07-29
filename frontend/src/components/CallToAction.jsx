import { Link } from 'react-router-dom';

export default function CallToAction() {
  return (
    <section className="cta-section">
      <h2>Ready to modernize your audit workflows?</h2>
      <Link to="/audit/new" className="btn-secondary" style={{ padding: '14px 32px', fontSize: '16px' }}>Try Now</Link>
    </section>
  );
}