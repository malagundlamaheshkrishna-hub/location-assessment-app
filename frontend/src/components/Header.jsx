import React from 'react';

function Header({ activeTab, setActiveTab, backendStatus }) {
  return (
    <header className="app-header">
      <div className="header-container">
        <div className="logo-group">
          <span className="app-icon">📍</span>
          <div>
            <h1 className="app-title">Location Assessment Tool</h1>
            <p className="app-subtitle">Full-Stack Prototype</p>
          </div>
        </div>

        <nav className="nav-tabs">
          <button
            className={`nav-btn ${activeTab === 'new' ? 'active' : ''}`}
            onClick={() => setActiveTab('new')}
          >
            New Assessment
          </button>
          <button
            className={`nav-btn ${activeTab === 'saved' ? 'active' : ''}`}
            onClick={() => setActiveTab('saved')}
          >
            Saved Assessments
          </button>
        </nav>

        <div className="status-badge-container">
          <span
            className={`status-pill ${
              backendStatus === 'healthy'
                ? 'status-online'
                : backendStatus === 'checking'
                ? 'status-checking'
                : 'status-offline'
            }`}
          >
            <span className="status-dot"></span>
            {backendStatus === 'healthy' ? 'API Connected' : backendStatus === 'checking' ? 'Connecting...' : 'API Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}

export default Header;
