import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Home from './pages/Home';
import NewAudit from './pages/NewAudit';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/audit" element={<NewAudit />} />
        <Route path="/audit/new" element={<Navigate to="/audit" replace />} />
        <Route path="*" element={<Navigate to="/audit" replace />} />
      </Routes>
    </Router>
  );
}

export default App;