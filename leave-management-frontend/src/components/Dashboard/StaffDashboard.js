import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { dashboardService } from '../../services/leaveService';
import Navigation from '../Common/Navigation';
import Calendar from '../Common/Calendar';
import Countdown from '../Common/Countdown';
import LeaveApplication from '../Leave/LeaveApplication';
import LeaveBalance from '../Leave/LeaveBalance';
import LeaveHistory from '../Leave/LeaveHistory';

const StaffDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { user } = useAuth();

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await dashboardService.getDashboardStats();
      setDashboardStats(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveApplicationSuccess = (response) => {
    // Refresh dashboard stats
    fetchDashboardStats();
    // Show success message
    alert(response.message);
    // Switch to history tab to see the new application
    setActiveTab('history');
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'apply', label: 'Apply for Leave', icon: '📝' },
    { id: 'balances', label: 'Leave Balances', icon: '⚖️' },
    { id: 'history', label: 'Leave History', icon: '📋' },
    { id: 'calendar', label: 'Calendar', icon: '📅' }
  ];

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--background-light)' }}>
      <Navigation />
      
      <div className="container" style={{ paddingTop: '2rem', paddingBottom: '2rem' }}>
        {/* Welcome Header */}
        <div className="card mb-4">
          <div style={{ padding: '1.5rem' }}>
            <h1 style={{ 
              fontSize: '2rem', 
              color: 'var(--primary-blue)', 
              marginBottom: '0.5rem' 
            }}>
              Welcome, {user?.first_name} {user?.last_name}
            </h1>
            <p style={{ 
              fontSize: '1.1rem', 
              color: 'var(--text-light)', 
              margin: 0 
            }}>
              Staff Dashboard - Employee #{user?.employee_number}
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="card mb-4">
          <div style={{ 
            display: 'flex', 
            overflowX: 'auto',
            borderBottom: '2px solid var(--border-light)',
            padding: '0 1rem'
          }}>
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '1rem 1.5rem',
                  border: 'none',
                  backgroundColor: 'transparent',
                  color: activeTab === tab.id ? 'var(--primary-blue)' : 'var(--text-light)',
                  fontWeight: activeTab === tab.id ? '600' : 'normal',
                  borderBottom: activeTab === tab.id ? '3px solid var(--primary-blue)' : '3px solid transparent',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  whiteSpace: 'nowrap',
                  fontSize: '1rem'
                }}
              >
                <span style={{ marginRight: '0.5rem' }}>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="fade-in">
          {activeTab === 'overview' && (
            <div>
              {/* Quick Stats */}
              {dashboardStats && (
                <div className="row mb-4">
                  <div className="col-12 col-md-3">
                    <div className="card text-center">
                      <div style={{ padding: '1.5rem' }}>
                        <div style={{ 
                          fontSize: '2.5rem', 
                          fontWeight: '700', 
                          color: 'var(--primary-blue)',
                          marginBottom: '0.5rem'
                        }}>
                          {dashboardStats.applications_this_year}
                        </div>
                        <div style={{ color: 'var(--text-light)' }}>
                          Applications This Year
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="col-12 col-md-3">
                    <div className="card text-center">
                      <div style={{ padding: '1.5rem' }}>
                        <div style={{ 
                          fontSize: '2.5rem', 
                          fontWeight: '700', 
                          color: 'var(--warning)',
                          marginBottom: '0.5rem'
                        }}>
                          {dashboardStats.pending_applications}
                        </div>
                        <div style={{ color: 'var(--text-light)' }}>
                          Pending Applications
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="col-12 col-md-3">
                    <div className="card text-center">
                      <div style={{ padding: '1.5rem' }}>
                        <div style={{ 
                          fontSize: '2.5rem', 
                          fontWeight: '700', 
                          color: 'var(--success)',
                          marginBottom: '0.5rem'
                        }}>
                          {dashboardStats.approved_applications}
                        </div>
                        <div style={{ color: 'var(--text-light)' }}>
                          Approved Applications
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="col-12 col-md-3">
                    <div className="card text-center">
                      <div style={{ padding: '1.5rem' }}>
                        <div style={{ 
                          fontSize: '2.5rem', 
                          fontWeight: '700', 
                          color: dashboardStats.currently_on_leave ? 'var(--accent-gold)' : 'var(--text-light)',
                          marginBottom: '0.5rem'
                        }}>
                          {dashboardStats.currently_on_leave ? '🏖️' : '💼'}
                        </div>
                        <div style={{ color: 'var(--text-light)' }}>
                          {dashboardStats.currently_on_leave ? 'On Leave' : 'At Work'}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Leave Status */}
              {dashboardStats?.currently_on_leave && (
                <div className="alert alert-info mb-4">
                  <h4 style={{ marginBottom: '0.5rem' }}>Currently on Leave</h4>
                  <p style={{ margin: 0 }}>
                    You are currently on {dashboardStats.currently_on_leave.leave_type_name} 
                    from {new Date(dashboardStats.currently_on_leave.start_date).toLocaleDateString()} 
                    to {new Date(dashboardStats.currently_on_leave.end_date).toLocaleDateString()}
                  </p>
                </div>
              )}

              {/* Upcoming Leaves */}
              {dashboardStats?.upcoming_leaves && dashboardStats.upcoming_leaves.length > 0 && (
                <div className="card mb-4">
                  <div className="card-header">
                    <h3 className="card-title">Upcoming Approved Leaves</h3>
                  </div>
                  <div style={{ padding: '1rem' }}>
                    {dashboardStats.upcoming_leaves.map((leave, index) => (
                      <div
                        key={index}
                        style={{
                          padding: '1rem',
                          backgroundColor: 'var(--background-light)',
                          borderRadius: '4px',
                          marginBottom: index < dashboardStats.upcoming_leaves.length - 1 ? '0.5rem' : 0,
                          border: '1px solid var(--border-light)'
                        }}
                      >
                        <div style={{ fontWeight: '600', color: 'var(--primary-blue)' }}>
                          {leave.leave_type_name}
                        </div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-light)' }}>
                          {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                          ({leave.days_requested} days)
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Main Content Grid */}
              <div className="row">
                <div className="col-12 col-lg-8">
                  <Calendar />
                </div>
                <div className="col-12 col-lg-4">
                  <Countdown />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'apply' && (
            <LeaveApplication onSuccess={handleLeaveApplicationSuccess} />
          )}

          {activeTab === 'balances' && (
            <LeaveBalance />
          )}

          {activeTab === 'history' && (
            <LeaveHistory />
          )}

          {activeTab === 'calendar' && (
            <div className="row">
              <div className="col-12 col-lg-8">
                <Calendar />
              </div>
              <div className="col-12 col-lg-4">
                <Countdown />
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card mt-4">
          <div className="card-header">
            <h3 className="card-title">Quick Actions</h3>
          </div>
          <div style={{ padding: '1rem' }}>
            <div className="btn-group">
              <button
                onClick={() => setActiveTab('apply')}
                className="btn btn-primary"
              >
                Apply for Leave
              </button>
              <button
                onClick={() => setActiveTab('balances')}
                className="btn btn-outline"
              >
                Check Balances
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className="btn btn-outline"
              >
                View History
              </button>
              <button
                onClick={fetchDashboardStats}
                className="btn btn-secondary"
                disabled={loading}
              >
                Refresh Data
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StaffDashboard;

