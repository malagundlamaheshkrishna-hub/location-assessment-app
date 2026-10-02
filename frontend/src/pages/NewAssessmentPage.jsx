import React, { useState } from 'react';
import AssessmentResult from '../components/AssessmentResult';
import { apiService } from '../services/api';

function NewAssessmentPage() {
  const [label, setLabel] = useState('');
  const [address, setAddress] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!address.trim()) {
      setError('Please provide a US Address.');
      return;
    }

    setError(null);
    setIsLoading(true);
    setResult(null);

    try {
      const payload = {
        label: label.trim() || null,
        address: address.trim(),
      };

      const data = await apiService.createAssessment(payload);
      setResult(data);
    } catch (err) {
      console.error('Assessment request failed:', err);
      let errorMsg = 'Failed to connect to the backend server.';
      if (err.response && err.response.data && err.response.data.detail) {
        errorMsg = err.response.data.detail;
      } else if (err.message) {
        errorMsg = err.message;
      }
      setError(`Error: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-container">
      <div className="card form-card">
        <h2 className="section-title">New Assessment</h2>
        <p className="section-description">
          Enter a US address to evaluate geographic elevation and current weather factors.
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit} className="assessment-form">
          <div className="form-group">
            <label htmlFor="label" className="form-label">
              Label
            </label>
            <input
              id="label"
              type="text"
              className="form-input"
              placeholder="e.g. Denver Office or Mountain Cabin"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="address" className="form-label">
              US Address <span className="required-star">*</span>
            </label>
            <input
              id="address"
              type="text"
              className="form-input"
              placeholder="e.g. 1437 Bannock St, Denver, CO"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? 'Assessing Location...' : 'Assess Location'}
          </button>
        </form>

        {isLoading && (
          <div className="loading-banner">
            <span className="spinner"></span>
            <span>Querying Census Geocoder, USGS Elevation & Open-Meteo Weather...</span>
          </div>
        )}
      </div>

      {result && <AssessmentResult assessment={result} />}
    </div>
  );
}

export default NewAssessmentPage;
