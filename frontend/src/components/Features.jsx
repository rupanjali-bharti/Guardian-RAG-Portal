export default function Features() {
  return (
    <section className="features" id="technology">
      <div className="section-header">
        <h2>Enterprise-Grade Architecture</h2>
        <p>Built for strict compliance environments requiring absolute precision.</p>
      </div>

      <div className="bento-grid">
        <div className="bento-card large">
          <i className="fa-solid fa-layer-group card-icon"></i>
          <h3>Advanced RAG Pipeline</h3>
          <p>Say goodbye to AI hallucinations. Guardian utilizes a strictly constrained Retrieval-Augmented Generation pipeline. Every answer provided in the dashboard is directly cited back to your uploaded reference files, ensuring total transparency.</p>
        </div>
        
        <div className="bento-card">
          <i className="fa-solid fa-network-wired card-icon"></i>
          <h3>Graph-Powered Context</h3>
          <p>By mapping your documents and complex policy relationships using Neo4j graph representations, the engine detects access gaps and systemic vulnerabilities that traditional linear scans miss.</p>
        </div>

        <div className="bento-card">
          <i className="fa-solid fa-microchip card-icon"></i>
          <h3>Agentic Orchestration</h3>
          <p>Powered by LangChain and LangGraph, the system deploys multi-agent workflows that automatically parse questionnaires and continuously monitor for systemic risks without manual intervention.</p>
        </div>

        <div className="bento-card large">
          <i className="fa-solid fa-lock card-icon"></i>
          <h3>Zero-Data Retention & RBAC</h3>
          <p>Your data remains yours. Our architecture enforces strict Role-Based Access Control and guarantees that your proprietary policy documents are fully isolated and never used to train public LLMs.</p>
        </div>
      </div>
    </section>
  );
}