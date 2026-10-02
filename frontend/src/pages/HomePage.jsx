import React, { useState, useEffect } from 'react';
import Header from '../components/Header';
import LocationForm from '../components/LocationForm';
import AssessmentList from '../components/AssessmentList';
import { apiService } from '../services/api';

function HomePage() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [assessments, setAssessments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    checkConnection();
    loadAssessments();
  }, []);

  const checkConnection = async () => {
    try {
      const res = await apiService.checkHealth();
      if (res.status === 'healthy') {
        setBackendStatus('healthy');
      } else {
        setBackendStatus('error');
      }
    } catch (err) {
      console.error('Failed to reach backend:', err);
      setBackendStatus('offline');
    }
  };

  const loadAssessments = async () => {
    setIsLoading(true);
    try {
      const data = await apiService.getAssessments();
      setAssessments(data);
    } catch (err) {
      console.error('Failed to load assessments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddAssessment = async (newLocation) => {
    setIsSubmitting(true);
    try {
      const created = await apiService.createAssessment(newLocation);
      setAssessments((prev) => [created, ...prev]);
      setNotification({
        type: 'success',
        message: `Successfully added "${created.address}" to SQLite database!`,
      });
      setTimeout(() => setNotification(null), 4000);
    } catch (err) {
      console.error('Failed to create assessment:', err);
      setNotification({
        type: 'error',
        message: 'Could not reach backend. Is FastAPI running on port 8000?',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="app-layout">
      <Header backendStatus={backendStatus} />

      <main className="main-content">
        {notification && (
          <div
            className={`alert ${
              notification.type === 'success' ? 'alert-success' : 'alert-error'
            }`}
          >
            {notification.message}
          </div>
        )}

        <div className="grid-container">
          <LocationForm
            onAddAssessment={handleAddAssessment}
            isSubmitting={isSubmitting}
          />
          <AssessmentList
            assessments={assessments}
            isLoading={isLoading}
            onRefresh={loadAssessments}
          />
        </div>
      </main>

      <footer className="app-footer">
        <p>Location Assessment Tool Prototype • FastAPI + React + SQLite</p>
      </footer>
    </div>
  );
}

export default HomePage;
