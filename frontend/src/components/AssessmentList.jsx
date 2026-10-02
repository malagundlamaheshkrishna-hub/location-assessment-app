import React from 'react';

function AssessmentList({ assessments, isLoading, onRefresh }) {
  const getStatusBadge = (status) => {
    switch (status) {
      case 'complete':
        return <span className="badge badge-success">Complete</span>;
      case 'partial':
        return <span className="badge badge-warning">Partial Data</span>;
      case 'failed':
        return <span className="badge badge-danger">Failed</span>;
      default:
        return <span className="badge badge-neutral">Pending</span>;
    }
  };

  return (
    <div className="card list-card">
      <div className="list-header">
        <div>
          <h2 className="section-title">Assessments in SQLite</h2>
          <p className="section-description">
            Assessment database records with status and non-zero scores.
          </p>
        </div>
        <button
          onClick={onRefresh}
          className="btn btn-secondary btn-sm"
          disabled={isLoading}
        >
          {isLoading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      {assessments.length === 0 ? (
        <div className="empty-state">
          <p className="empty-title">No assessments yet</p>
          <p className="empty-subtitle">
            Add an address above to store a new assessment in SQLite.
          </p>
        </div>
      ) : (
        <div className="table-responsive">
          <table className="assessments-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Label / Address</th>
                <th>Coordinates</th>
                <th>Elev / Temp</th>
                <th>Score</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {assessments.map((item) => (
                <tr key={item.id}>
                  <td className="font-mono">#{item.id}</td>
                  <td>
                    {item.label && <div className="font-semibold">{item.label}</div>}
                    <div className="text-secondary">{item.address}</div>
                  </td>
                  <td className="text-secondary">
                    {item.latitude !== null && item.longitude !== null
                      ? `${item.latitude}, ${item.longitude}`
                      : 'Unavailable'}
                  </td>
                  <td className="text-secondary">
                    <div>Elev: {item.elevation !== null ? `${item.elevation} ft` : 'N/A'}</div>
                    <div>Temp: {item.temperature !== null ? `${item.temperature}°C` : 'N/A'}</div>
                  </td>
                  <td>
                    {item.total_score !== null ? (
                      <span className="font-semibold text-primary">{item.total_score}</span>
                    ) : (
                      <span className="text-muted">N/A</span>
                    )}
                  </td>
                  <td>{getStatusBadge(item.status)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AssessmentList;
