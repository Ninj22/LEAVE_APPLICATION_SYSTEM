import React, { useState, useEffect } from 'react';
import { leaveService } from '../../services/leaveService';
import { useAuth } from '../../contexts/AuthContext';

const PendingApprovals = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processingId, setProcessingId] = useState(null);
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [comments, setComments] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    fetchPendingApplications();
  }, []);

  const fetchPendingApplications = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await leaveService.getPendingApplications();
      setApplications(data.applications);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveReject = async (applicationId, action) => {
    try {
      setProcessingId(applicationId);
      setError('');
      
      await leaveService.approveRejectApplication(applicationId, action, comments);
      
      // Remove the processed application from the list
      setApplications(prev => prev.filter(app => app.id !== applicationId));
      
      // Reset form
      setSelectedApplication(null);
      setComments('');
      
    } catch (error) {
      setError(error.message);
    } finally {
      setProcessingId(null);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateTime = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRoleDisplayName = (role) => {
    switch (role) {
      case 'staff':
        return 'Staff';
      case 'hod':
        return 'Head of Department';
      case 'principal_secretary':
        return 'Principal Secretary';
      default:
        return role;
    }
  };

  const getApprovalLevel = () => {
    if (user?.role === "hod") {
      return "Staff Applications (Pending HOD Approval)";
    } else if (user?.role === 'principal_secretary') {
      return "Applications (Pending Principal Secretary Approval)";
    }
    return 'Applications';
  };

  return (
    <div className="card">
      <div className="card-header">
        <div className="d-flex justify-between align-center">
          <h3 className="card-title">Pending Approvals - {getApprovalLevel()}</h3>
          <button 
            onClick={fetchPendingApplications}
            className="btn btn-sm btn-outline"
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center p-4">
          <div className="loading">Loading pending applications...</div>
        </div>
      ) : applications.length === 0 ? (
        <div className="text-center p-4">
          <div style={{ color: 'var(--text-light)', fontSize: '1.1rem' }}>
            No pending applications
          </div>
          <p style={{ color: 'var(--text-light)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            All applications have been processed
          </p>
        </div>
      ) : (
        <div>
          {/* Applications List */}
          <div style={{ padding: '1rem' }}>
            {applications.map((application) => (
              <div
                key={application.id}
                style={{
                  border: '2px solid var(--border-light)',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  marginBottom: '1rem',
                  backgroundColor: selectedApplication?.id === application.id ? 'rgba(0, 51, 102, 0.05)' : 'var(--white)',
                  transition: 'all 0.3s ease'
                }}
              >
                {/* Application Header */}
                <div className="row mb-3">
                  <div className="col-12 col-md-8">
                    <h4 style={{ 
                      fontSize: '1.2rem', 
                      color: 'var(--primary-blue)', 
                      marginBottom: '0.5rem' 
                    }}>
                      {application.applicant_name}
                    </h4>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-light)' }}>
                      Employee #{application.user_id} • Applied on {formatDateTime(application.created_at)}
                    </div>
                  </div>
                  <div className="col-12 col-md-4 text-right">
                    <span className="badge badge-pending">
                      {application.display_status}
                    </span>
                  </div>
                </div>

                {/* Leave Details */}
                <div className="row mb-3">
                  <div className="col-12 col-md-3">
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                        Leave Type
                      </div>
                      <div style={{ color: 'var(--primary-blue)', fontWeight: '600' }}>
                        {application.leave_type_name}
                      </div>
                    </div>
                  </div>
                  <div className="col-12 col-md-3">
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                        Duration
                      </div>
                      <div style={{ color: 'var(--primary-blue)', fontWeight: '600' }}>
                        {application.days_requested} days
                      </div>
                    </div>
                  </div>
                  <div className="col-12 col-md-6">
                    <div style={{ marginBottom: '1rem' }}>
                      <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                        Leave Period
                      </div>
                      <div style={{ color: 'var(--primary-blue)', fontWeight: '600' }}>
                        {formatDate(application.start_date)} - {formatDate(application.end_date)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Additional Details */}
                <div className="row mb-3">
                  {application.contact_info && (
                    <div className="col-12 col-md-6">
                      <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                          Contact Information
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-light)' }}>
                          {application.contact_info}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {application.person_handling_duties_name && (
                    <div className="col-12 col-md-6">
                      <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                          Duties Handled By
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-light)' }}>
                          {application.person_handling_duties_name}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {application.last_leave_from && application.last_leave_to && (
                  <div className="row mb-3">
                    <div className="col-12">
                      <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                          Last Leave Period
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-light)' }}>
                          {formatDate(application.last_leave_from)} - {formatDate(application.last_leave_to)}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {application.permission_note_country && (
                  <div className="row mb-3">
                    <div className="col-12">
                      <div style={{ marginBottom: '1rem' }}>
                        <div style={{ fontWeight: '600', color: 'var(--text-dark)' }}>
                          Permission Note (Leaving Country)
                        </div>
                        <div style={{ 
                          fontSize: '0.9rem', 
                          color: 'var(--text-light)',
                          padding: '0.5rem',
                          backgroundColor: 'var(--background-light)',
                          borderRadius: '4px'
                        }}>
                          {application.permission_note_country}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Approval Section */}
                <div style={{
                  borderTop: '1px solid var(--border-light)',
                  paddingTop: '1rem',
                  marginTop: '1rem'
                }}>
                  {selectedApplication?.id === application.id ? (
                    <div>
                      <div className="form-group">
                        <label className="form-label">Comments (Optional)</label>
                        <textarea
                          className="form-textarea"
                          value={comments}
                          onChange={(e) => setComments(e.target.value)}
                          placeholder="Add comments about your decision..."
                          rows="3"
                        />
                      </div>
                      
                      <div className="btn-group">
                        <button
                          onClick={() => handleApproveReject(application.id, 'approve')}
                          className="btn btn-success"
                          disabled={processingId === application.id}
                        >
                          {processingId === application.id ? 'Processing...' : 'Approve'}
                        </button>
                        <button
                          onClick={() => handleApproveReject(application.id, 'reject')}
                          className="btn btn-danger"
                          disabled={processingId === application.id}
                        >
                          {processingId === application.id ? 'Processing...' : 'Reject'}
                        </button>
                        <button
                          onClick={() => {
                            setSelectedApplication(null);
                            setComments('');
                          }}
                          className="btn btn-secondary"
                          disabled={processingId === application.id}
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="btn-group">
                      <button
                        onClick={() => setSelectedApplication(application)}
                        className="btn btn-primary"
                        disabled={processingId !== null}
                      >
                        Review Application
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div style={{
            padding: '1rem',
            backgroundColor: 'var(--background-light)',
            borderTop: '1px solid var(--border-light)'
          }}>
            <div className="text-center">
              <div style={{ fontWeight: '600', fontSize: '1.2rem', color: 'var(--primary-blue)' }}>
                {applications.length} application{applications.length !== 1 ? 's' : ''} pending your approval
              </div>
              <div style={{ fontSize: '0.9rem', color: 'var(--text-light)', marginTop: '0.25rem' }}>
                Review each application carefully before making a decision
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PendingApprovals;

