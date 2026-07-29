export default function SecuritySection() {
  return (
    <section className="features" id="security">
      <div className="section-header">
        <h2>Security & Compliance by Design</h2>
        <p>Every audit is built with trust, traceability, and controlled access in mind.</p>
      </div>

      <div className="bento-grid">
        <div className="bento-card large">
          <i className="fa-solid fa-user-shield card-icon"></i>
          <h3>Role-Based Access Control</h3>
          <p>Admins, reviewers, and auditors work in clearly scoped environments so sensitive policies and findings stay visible only to the right people.</p>
        </div>

        <div className="bento-card">
          <i className="fa-solid fa-file-contract card-icon"></i>
          <h3>Evidence-Based Audits</h3>
          <p>Every response is anchored to uploaded policies and questionnaires, giving compliance teams full traceability for each finding and decision.</p>
        </div>

        <div className="bento-card">
          <i className="fa-solid fa-shield-halved card-icon"></i>
          <h3>Protected Knowledge Base</h3>
          <p>Uploaded documents remain isolated to the audit session and are not used for public model training, helping protect proprietary information.</p>
        </div>

        <div className="bento-card large">
          <i className="fa-solid fa-lock-open card-icon"></i>
          <h3>Transparent Review Workflow</h3>
          <p>Compliance teams can inspect the AI-generated answer, review the cited source, and validate gaps with a clear visual audit trail.</p>
        </div>
      </div>
    </section>
  );
}
