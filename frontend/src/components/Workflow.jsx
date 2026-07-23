export default function Workflow() {
  return (
    <section className="pipeline-section" id="workflow">
      <div className="section-header">
        <h2>The Audit Workflow</h2>
        <p>From unstructured policies to interactive, grounded insights in three automated steps.</p>
      </div>

      <div className="pipeline-step">
        <div className="step-number">1</div>
        <div className="step-content">
          <h3><i className="fa-solid fa-file-arrow-up"></i> Ingest & Embed</h3>
          <p>Upload your corporate directories, security protocols, and privacy text files into the portal. The system instantly chunks the unstructured data and generates vector embeddings for high-speed semantic search.</p>
          <div className="code-snippet">&gt; File 'security_policy.txt' successfully embedded and mapped.</div>
        </div>
      </div>

      <div className="pipeline-step">
        <div className="step-number">2</div>
        <div className="step-content">
          <h3><i className="fa-solid fa-diagram-project"></i> Orchestrate & Link</h3>
          <p>The backend utilizes advanced LangChain and LangGraph orchestration to dynamically route queries. It cross-references policies and maps entity relationships using a Neo4j knowledge graph structure to ensure no context is lost.</p>
          <div className="code-snippet">&gt; Initializing multi-agent graph reasoning... Complete.</div>
        </div>
      </div>

      <div className="pipeline-step">
        <div className="step-number">3</div>
        <div className="step-content">
          <h3><i className="fa-solid fa-check-double"></i> Audit & Verify</h3>
          <p>Query the system through the dashboard. The portal identifies compliance gaps, provides verified answers, and delivers exact source citations so human auditors can trust the output.</p>
          <div className="code-snippet">&gt; Compliance Score: 82% | 9 Items Verified | 2 Gaps Found</div>
        </div>
      </div>
    </section>
  );
}