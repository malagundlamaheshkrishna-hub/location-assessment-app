import React from 'react';

function AssessmentResult({ assessment }) {
  if (!assessment) return null;

  const {
    id,
    label,
    address,
    latitude,
    longitude,
    elevation,
    temperature,
    elevation_score,
    temperature_score,
    total_score,
    status,
    created_at,
  } = assessment;

  // Compute maximum available points based on what is available
  let maxPossiblePoints = 0;
  if (elevation_score !== null) maxPossiblePoints += 40;
  if (temperature_score !== null) maxPossiblePoints += 60;

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

  return (
    <div className="card result-card">
      <div className="result-header">
        <div>
          <span className="result-badge">Assessment Result #{id}</span>
          <h2 className="result-title">{label || address}</h2>
          {label && <p className="result-subtitle">{address}</p>}
        </div>
        <div className="score-badge-box">
          <span className="score-label">Overall Score</span>
          <div className="score-value-container">
            {total_score !== null ? (
              <span className="score-number">
                {total_score} <span className="score-max">/ {maxPossiblePoints} pts</span>
              </span>
            ) : (
              <span className="score-unavailable">Unavailable</span>
            )}
          </div>
          <span className={`status-tag status-tag-${status}`}>
            {status === 'complete' ? 'Complete Data' : status === 'partial' ? 'Partial Data' : 'Unavailable'}
          </span>
        </div>
      </div>

      {/* Partial Data Notice Banner */}
      {status === 'partial' && (
        <div className="notice-banner notice-warning">
          <span className="notice-icon">⚠️</span>
          <div>
            <strong>Partially Unavailable Data:</strong> One or more data sources were unavailable. The overall score was computed strictly from available factors, and missing factors were <strong>not</strong> treated as zero.
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div className="notice-banner notice-danger">
          <span className="notice-icon">❌</span>
          <div>
            <strong>Unavailable Assessment:</strong> Geocoding or external data services could not retrieve data for this address.
          </div>
        </div>
      )}

      {/* Coordinates & Metadata */}
      <div className="info-grid">
        <div className="info-box">
          <span className="info-label">Latitude</span>
          <span className="info-value">
            {latitude !== null && latitude !== undefined ? latitude : <span className="text-unavailable">Unavailable</span>}
          </span>
        </div>
        <div className="info-box">
          <span className="info-label">Longitude</span>
          <span className="info-value">
            {longitude !== null && longitude !== undefined ? longitude : <span className="text-unavailable">Unavailable</span>}
          </span>
        </div>
        <div className="info-box">
          <span className="info-label">Created Date</span>
          <span className="info-value">{formatDate(created_at)}</span>
        </div>
        <div className="info-box">
          <span className="info-label">Status</span>
          <span className="info-value capitalize">{status}</span>
        </div>
      </div>

      <hr className="divider" />

      {/* Factor Breakdown Table */}
      <h3 className="breakdown-title">Factor Breakdown</h3>
      <div className="table-responsive">
        <table className="breakdown-table">
          <thead>
            <tr>
              <th>Factor</th>
              <th>Raw Value</th>
              <th>Points</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Elevation</strong></td>
              <td>
                {elevation !== null && elevation !== undefined ? (
                  `${elevation} ft`
                ) : (
                  <span className="text-unavailable">Unavailable</span>
                )}
              </td>
              <td>
                {elevation_score !== null && elevation_score !== undefined ? (
                  <strong className="text-primary">{elevation_score} / 40</strong>
                ) : (
                  <span className="text-unavailable">Unavailable</span>
                )}
              </td>
              <td>
                <span className="source-tag">USGS</span>
              </td>
            </tr>

            <tr>
              <td><strong>Temperature</strong></td>
              <td>
                {temperature !== null && temperature !== undefined ? (
                  `${temperature} °C`
                ) : (
                  <span className="text-unavailable">Unavailable</span>
                )}
              </td>
              <td>
                {temperature_score !== null && temperature_score !== undefined ? (
                  <strong className="text-primary">{temperature_score} / 60</strong>
                ) : (
                  <span className="text-unavailable">Unavailable</span>
                )}
              </td>
              <td>
                <span className="source-tag">Open-Meteo</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default AssessmentResult;
