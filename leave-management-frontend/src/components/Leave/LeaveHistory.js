import React, { useState, useEffect } from 'react';
import { leaveService } from '../../services/leaveService';

const LeaveHistory = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    year: new Date().getFullYear()
  });

  useEffect(() => {
    fetchLeaveHistory();
  }, [filters]);

  const fetchLeaveHistory = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await leaveService.getLeaveHistory(filters);
      setApplications(data.history);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending_hod_approval: { class: "badge-pending", text: "Pending HOD Approval" },
      pending_principal_secretary_approval: { class: "badge-pending", text: "Pending PS Approval" },
      approved: { class: "badge-approved", text: "Approved" },
      rejected: { class: "badge-rejected", text: "Rejected" }
    };

    const config = statusConfig[status] || { class: "badge-info", text: status };
    
    return (
      <span className={`badge ${config.class}`}>
        {config.text}
      </span>
    );
  };
  
  const handleDownloadPdf = async (applicationId) => {
    try {
      const response = await leaveService.downloadPdf(applicationId);
      const blob = new Blob([response], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `leave_application_${applicationId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      setError(error.message);
    }
  };
  
  
  const generateYearOptions = () => {
    const currentYear = new Date().getFullYear();
    const years = [];
    for (let year = currentYear; year >= currentYear - 5; year--) {
      years.push(year);
    }
    return years;
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="d-flex justify-between align-center flex-wrap" style={{ gap: '1rem' }}>
          <h3 className="card-title">Leave History</h3>
          
          {/* Filters */}
          <div className="d-flex align-center flex-wrap" style={{ gap: '1rem' }}>
            <div>
              <select
                name="status"
                value={filters.status}
                onChange={handleFilterChange}
                className="form-select"
                style={{ minWidth: '120px' }}
              >
                <option value="">All Status</option>
                <option value="pending_hod_approval">Pending HOD Approval</option>
                <option value="pending_principal_secretary_approval">Pending PS Approval</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            
            <div>
              <select
                name="year"
                value={filters.year}
                onChange={handleFilterChange}
                className="form-select"
                style={{ minWidth: '100px' }}
              >
                {generateYearOptions().map(year => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </div>

            <button 
              onClick={fetchLeaveHistory}
              className="btn btn-sm btn-outline"
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center p-4">
          <div className="loading">Loading history...</div>
        </div>
      ) : applications.length === 0 ? (
        <div className="text-center p-4">
          <div style={{ color: 'var(--text-light)', fontSize: '1.1rem' }}>
            No leave applications found
          </div>
          <p style={{ color: 'var(--text-light)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            {filters.status || filters.year !== new Date().getFullYear() 
              ? 'Try adjusting your filters' 
              : 'Your leave applications will appear here'}
          </p>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Leave Type</th>
                <th>Dates</th>
                <th>Days</th>
                <th>Status</th>
                <th>Applied On</th>
                <th>Approved By</th>
                <th>Comments</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr key={application.id}>
                  <td>
                    <div style={{ fontWeight: '600' }}>
                      {application.leave_type_name}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.875rem' }}>
                      <div>{formatDate(application.start_date)}</div>
                      <div style={{ color: 'var(--text-light)' }}>
                        to {formatDate(application.end_date)}
                      </div>
                    </div>
                  </td>
                  <td>
                    <div style={{ 
                      fontWeight: '600',
                      color: 'var(--primary-blue)'
                    }}>
                      {application.days_requested}
                    </div>
                  </td>
                  <td>
                    {getStatusBadge(application.status)}
                    {application.status === 'approved' && (
                      <button
                        onClick={() => handleDownloadPdf(application.id)}
                        className="btn btn-sm btn-outline-primary mt-2"
                        style={{ fontSize: '0.75rem' }}
                      >
                        Download PDF
                      </button>
                    )}
                  </td>
                  <td>
                    <div style={{ fontSize: '0.875rem' }}>
                      {formatDate(application.created_at)}
                    </div>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.875rem' }}>
                      {application.approver_name ? (
                        <>
                          <div>{application.approver_name}</div>
                          {application.approval_date && (
                            <div style={{ color: 'var(--text-light)' }}>
                              {formatDate(application.approval_date)}
                            </div>
                          )}
                        </>
                      ) : (
                        <span style={{ color: 'var(--text-light)' }}>-</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <div style={{ 
                      fontSize: '0.875rem',
                      maxWidth: '200px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {application.comments ? (
                        <span title={application.comments}>
                          {application.comments}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--text-light)' }}>-</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Summary Statistics */}
      {applications.length > 0 && (
        <div style={{
          padding: '1rem',
          backgroundColor: 'var(--background-light)',
          borderTop: '1px solid var(--border-light)'
        }}>
          <div className="row">
            <div className="col-3 text-center">
              <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--primary-blue)' }}>
                {applications.length}
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-light)' }}>
                Total Applications
              </div>
            </div>
            <div className="col-3 text-center">
              <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--success)' }}>
                {applications.filter(app => app.status === 'approved').length}
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-light)' }}>
                Approved
              </div>
            </div>
            <div className="col-3 text-center">
              <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--warning)' }}>
                {applications.filter(app => app.status === 'pending').length}
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-light)' }}>
                Pending
              </div>
            </div>
            <div className="col-3 text-center">
              <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--danger)' }}>
                {applications.filter(app => app.status === 'rejected').length}
              </div>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-light)' }}>
                Rejected
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeaveHistory;

