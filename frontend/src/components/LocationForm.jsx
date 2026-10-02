import React, { useState } from 'react';

function LocationForm({ onAddAssessment, isSubmitting }) {
  const [address, setAddress] = useState('');
  const [label, setLabel] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!address.trim()) {
      setError('Please enter a location address.');
      return;
    }

    setError('');
    onAddAssessment({
      address: address.trim(),
      label: label.trim() || null,
      latitude: latitude ? parseFloat(latitude) : null,
      longitude: longitude ? parseFloat(longitude) : null,
    });

    setAddress('');
    setLabel('');
    setLatitude('');
    setLongitude('');
  };

  return (
    <div className="card form-card">
      <h2 className="section-title">New Assessment</h2>
      <p className="section-description">
        Create an assessment record in SQLite.
      </p>

      {error && <div className="alert-error">{error}</div>}

      <form onSubmit={handleSubmit} className="assessment-form">
        <div className="form-group">
          <label htmlFor="address" className="form-label">
            Address / Location <span className="required-star">*</span>
          </label>
          <input
            id="address"
            type="text"
            className="form-input"
            placeholder="e.g. 1600 Amphitheatre Pkwy, Mountain View, CA"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-group">
          <label htmlFor="label" className="form-label">
            Label / Nickname (Optional)
          </label>
          <input
            id="label"
            type="text"
            className="form-input"
            placeholder="e.g. Headquarters or Warehouse A"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            disabled={isSubmitting}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="latitude" className="form-label">
              Latitude (Optional)
            </label>
            <input
              id="latitude"
              type="number"
              step="any"
              className="form-input"
              placeholder="e.g. 37.4220"
              value={latitude}
              onChange={(e) => setLatitude(e.target.value)}
              disabled={isSubmitting}
            />
          </div>

          <div className="form-group">
            <label htmlFor="longitude" className="form-label">
              Longitude (Optional)
            </label>
            <input
              id="longitude"
              type="number"
              step="any"
              className="form-input"
              placeholder="e.g. -122.0841"
              value={longitude}
              onChange={(e) => setLongitude(e.target.value)}
              disabled={isSubmitting}
            />
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : 'Create Assessment'}
        </button>
      </form>
    </div>
  );
}

export default LocationForm;
