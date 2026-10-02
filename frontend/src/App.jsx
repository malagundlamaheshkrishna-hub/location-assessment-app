import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import NewAssessmentPage from './pages/NewAssessmentPage';
import SavedAssessmentsPage from './pages/SavedAssessmentsPage';
import { apiService } from './services/api';

function App() {
  const [activeTab, setActiveTab] = useState('new');
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    checkBackendHealth();
  }, []);

  const checkBackendHealth = async () => {
    try {
      const res = await apiService.checkHealth();
      if (res.status === 'healthy') {
        setBackendStatus('healthy');
      } else {
        setBackendStatus('error');
      }
    } catch (err) {
      console.warn('Backend is currently unreachable:', err);
      setBackendStatus('offline');
    }
  };

  return (
    <div className="app-layout">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        backendStatus={backendStatus}
      />

      <main className="main-content">
        {activeTab === 'new' ? (
          <NewAssessmentPage />
        ) : (
          <SavedAssessmentsPage />
        )}
      </main>

      <footer className="app-footer">
        <p>Location Assessment Tool Prototype • React + FastAPI + SQLite</p>
      </footer>
    </div>
  );
}

export default App;
