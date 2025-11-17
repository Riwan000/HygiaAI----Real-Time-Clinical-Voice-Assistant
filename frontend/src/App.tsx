/**
 * Main App Component
 * 
 * Sets up routing and application structure.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { SOAPNotes } from './pages/SOAPNotes';
import { Transcription } from './pages/Transcription';
import { Analytics } from './pages/Analytics';
import { Timeline } from './pages/Timeline';
import { Knowledge } from './pages/Knowledge';
import { Settings } from './pages/Settings';
import { MultimodalInput } from './pages/MultimodalInput';
import { CaseViewer } from './pages/CaseViewer';

function App() {
  try {
    return (
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/soap-notes" element={<SOAPNotes />} />
            <Route path="/transcription" element={<Transcription />} />
            <Route path="/multimodal-input" element={<MultimodalInput />} />
            <Route path="/case-viewer" element={<CaseViewer />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/timeline" element={<Timeline />} />
            <Route path="/knowledge" element={<Knowledge />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    );
  } catch (error) {
    console.error('App render error:', error);
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h1>Error rendering app</h1>
        <pre>{String(error)}</pre>
      </div>
    );
  }
}

export default App;
