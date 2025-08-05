import React, { useState, useEffect } from 'react';
import { leaveService } from '../../services/leaveService';

const LeaveBalance = () => {
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchLeaveBalances();
  }, []);

  const fetchLeaveBalances = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await leaveService.getLeaveBalances();
      setBalances(data.balances);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getBalanceStatus = (balance, maxDays) => {
    const percentage = (balance / maxDays) * 100;
    if (percentage >= 75) return 'high';
    if (percentage >= 25) return 'medium';
    return 'low';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'high':
        return 'var(--success)';
      case 'medium':
        return 'var(--warning)';
      case 'low':
        return 'var(--danger)';
      default:
        return 'var(--text-light)';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'high':
        return 'Good';
      case 'medium':
        return 'Moderate';
      case 'low':
        return 'Low';
      default:
        return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Balances</h3>
        </div>
        <div className="text-center p-4">
          <div className="loading">Loading balances...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Balances</h3>
        </div>
        <div className="alert alert-error">
          {error}
        </div>
        <div className="text-center p-2">
          <button 
            onClick={fetchLeaveBalances}
            className="btn btn-primary btn-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="d-flex justify-between align-center">
          <h3 className="card-title">Leave Balances ({new Date().getFullYear()})</h3>
          <button 
            onClick={fetchLeaveBalances}
            className="btn btn-sm btn-outline"
            disabled={loading}
          >
            Refresh
          </button>
        </div>
      </div>

      {balances.length === 0 ? (
        <div className="text-center p-4">
          <div style={{ color: 'var(--text-light)', fontSize: '1.1rem' }}>
            No leave balances found
          </div>
          <p style={{ color: 'var(--text-light)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Leave balances will be initialized when you sign up
          </p>
        </div>
      ) : (
        <div style={{ padding: '1rem' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
            gap: '1rem'
          }}>
            {balances.map((balance) => {
              const leaveType = balance.leave_type_name || 'Unknown Leave Type';
              const maxDays = 30; // Default, should come from leave type
              const status = getBalanceStatus(balance.balance_days, maxDays);
              const percentage = Math.min((balance.balance_days / maxDays) * 100, 100);

              return (
                <div
                  key={balance.id}
                  style={{
                    padding: '1.5rem',
                    backgroundColor: 'var(--background-light)',
                    borderRadius: '8px',
                    border: '2px solid var(--border-light)',
                    transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 4px 12px var(--shadow)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  {/* Leave Type Header */}
                  <div style={{ marginBottom: '1rem' }}>
                    <h4 style={{
                      fontSize: '1.1rem',
                      fontWeight: '600',
                      color: 'var(--primary-blue)',
                      marginBottom: '0.25rem'
                    }}>
                      {leaveType}
                    </h4>
                    <div style={{
                      fontSize: '0.875rem',
                      color: 'var(--text-light)'
                    }}>
                      Year: {balance.year}
                    </div>
                  </div>

                  {/* Balance Display */}
                  <div style={{ marginBottom: '1rem' }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'baseline',
                      marginBottom: '0.5rem'
                    }}>
                      <span style={{
                        fontSize: '2rem',
                        fontWeight: '700',
                        color: getStatusColor(status)
                      }}>
                        {balance.balance_days}
                      </span>
                      <span style={{
                        fontSize: '0.875rem',
                        color: 'var(--text-light)'
                      }}>
                        days remaining
                      </span>
                    </div>

                    {/* Progress Bar */}
                    <div style={{
                      width: '100%',
                      height: '8px',
                      backgroundColor: 'var(--border-light)',
                      borderRadius: '4px',
                      overflow: 'hidden',
                      marginBottom: '0.5rem'
                    }}>
                      <div style={{
                        width: `${percentage}%`,
                        height: '100%',
                        backgroundColor: getStatusColor(status),
                        transition: 'width 0.3s ease'
                      }} />
                    </div>

                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '0.875rem',
                      color: 'var(--text-light)'
                    }}>
                      <span>0 days</span>
                      <span>{maxDays} days</span>
                    </div>
                  </div>

                  {/* Status Badge */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}>
                    <span
                      className="badge"
                      style={{
                        backgroundColor: getStatusColor(status),
                        color: status === 'medium' ? 'var(--text-dark)' : 'var(--white)',
                        fontSize: '0.75rem',
                        padding: '0.25rem 0.75rem'
                      }}
                    >
                      {getStatusText(status)} Balance
                    </span>
                    <span style={{
                      fontSize: '0.875rem',
                      color: 'var(--text-light)'
                    }}>
                      {Math.round(percentage)}%
                    </span>
                  </div>

                  {/* Usage Information */}
                  <div style={{
                    marginTop: '1rem',
                    padding: '0.75rem',
                    backgroundColor: 'var(--white)',
                    borderRadius: '4px',
                    fontSize: '0.875rem'
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: '0.25rem'
                    }}>
                      <span style={{ color: 'var(--text-light)' }}>Allocated:</span>
                      <span style={{ fontWeight: '600' }}>{maxDays} days</span>
                    </div>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginBottom: '0.25rem'
                    }}>
                      <span style={{ color: 'var(--text-light)' }}>Used:</span>
                      <span style={{ fontWeight: '600' }}>{maxDays - balance.balance_days} days</span>
                    </div>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between'
                    }}>
                      <span style={{ color: 'var(--text-light)' }}>Remaining:</span>
                      <span style={{ 
                        fontWeight: '600',
                        color: getStatusColor(status)
                      }}>
                        {balance.balance_days} days
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Summary */}
          <div style={{
            marginTop: '1.5rem',
            padding: '1rem',
            backgroundColor: 'var(--white)',
            borderRadius: '8px',
            border: '2px solid var(--primary-blue)'
          }}>
            <h4 style={{
              fontSize: '1rem',
              color: 'var(--primary-blue)',
              marginBottom: '0.75rem'
            }}>
              Balance Summary
            </h4>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
              gap: '1rem',
              fontSize: '0.875rem'
            }}>
              <div className="text-center">
                <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--primary-blue)' }}>
                  {balances.reduce((total, balance) => total + balance.balance_days, 0)}
                </div>
                <div style={{ color: 'var(--text-light)' }}>Total Days Remaining</div>
              </div>
              <div className="text-center">
                <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--success)' }}>
                  {balances.filter(b => getBalanceStatus(b.balance_days, 30) === 'high').length}
                </div>
                <div style={{ color: 'var(--text-light)' }}>Good Balances</div>
              </div>
              <div className="text-center">
                <div style={{ fontWeight: '600', fontSize: '1.5rem', color: 'var(--danger)' }}>
                  {balances.filter(b => getBalanceStatus(b.balance_days, 30) === 'low').length}
                </div>
                <div style={{ color: 'var(--text-light)' }}>Low Balances</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LeaveBalance;

