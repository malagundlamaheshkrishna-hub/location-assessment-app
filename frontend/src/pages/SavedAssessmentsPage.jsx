import React, { useState, useEffect } from 'react';
import AssessmentDetailPage from './AssessmentDetailPage';
import { apiService } from '../services/api';

function SavedAssessmentsPage() {
  const [assessments, setAssessments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);

  useEffect(() => {
    fetchAssessments();
  }, []);

  const fetchAssessments = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiService.getAssessments();
      setAssessments(data);
    } catch (err) {
      console.error('Failed to load assessments:', err);
      let msg = 'Failed to load saved assessments.';
      if (err.response && err.response.data && err.response.data.detail) {
        msg = err.response.data.detail;
      } else if (err.message) {
        msg = err.message;
      }
      setError(`Error: ${msg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'complete':
        return <span className="badge badge-success">Complete</span>;
      case 'partial':
        return <span className="badge badge-warning">Partial</span>;
      default:
        return <span className="badge badge-danger">Unavailable</span>;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '—';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  // If viewing an assessment detail, render the AssessmentDetailPage
  if (selectedAssessmentId !== null) {
    return (
      <AssessmentDetailPage
        assessmentId={selectedAssessmentId}
        onBack={() => setSelectedAssessmentId(null)}
      />
    );
  }

  return (
    <div className="page-container">
      <div className="card list-card">
        <div className="list-header">
          <div>
            <h2 className="section-title">Saved Assessments</h2>
            <p className="section-description">
              Browse previously evaluated locations stored in the database.
            </p>
          </div>
          <button
            onClick={fetchAssessments}
            className="btn btn-secondary btn-sm"
            disabled={isLoading}
          >
            {isLoading ? 'Refreshing...' : '↻ Refresh'}
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {isLoading ? (
          <div className="loading-state">
            <span className="spinner"></span> Loading saved assessments...
          </div>
        ) : assessments.length === 0 ? (
          <div className="empty-state">
            <p className="empty-title">No assessments yet.</p>
            <p className="empty-subtitle">
              Create a new assessment to see it listed here.
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="assessments-table">
              <thead>
                <tr>
                  <th>Label</th>
                  <th>Address</th>
                  <th>Score</th>
                  <th>Status</th>
                  <th>Created Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {assessments.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <span className="font-semibold">
                        {item.label ? item.label : <span className="text-muted">—</span>}
                      </span>
                    </td>
                    <td className="text-address">{item.address}</td>
                    <td>
                      {item.total_score !== null ? (
                        <strong className="text-primary">{item.total_score} pts</strong>
                      ) : (
                        <span className="text-unavailable">Unavailable</span>
                      )}
                    </td>
                    <td>{getStatusBadge(item.status)}</td>
                    <td className="text-secondary">{formatDate(item.created_at)}</td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => setSelectedAssessmentId(item.id)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default SavedAssessmentsPage;
