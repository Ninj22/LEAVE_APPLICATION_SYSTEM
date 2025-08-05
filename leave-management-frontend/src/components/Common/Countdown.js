import React, { useState, useEffect } from 'react';
import { dashboardService } from '../../services/leaveService';

const Countdown = () => {
  const [countdownData, setCountdownData] = useState(null);
  const [timeLeft, setTimeLeft] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCountdownData();
  }, []);

  useEffect(() => {
    if (countdownData?.countdown) {
      const timer = setInterval(() => {
        updateTimeLeft();
      }, 1000);

      return () => clearInterval(timer);
    }
  }, [countdownData]);

  const fetchCountdownData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getLeaveCountdown();
      setCountdownData(data);
      if (data.countdown) {
        updateTimeLeft(data.countdown);
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const updateTimeLeft = (countdown = countdownData?.countdown) => {
    if (!countdown) return;

    const now = new Date().getTime();
    let targetDate;

    if (countdown.type === 'current_leave') {
      targetDate = new Date(countdown.end_date + 'T23:59:59').getTime();
    } else {
      targetDate = new Date(countdown.start_date + 'T00:00:00').getTime();
    }

    const difference = targetDate - now;

    if (difference > 0) {
      setTimeLeft({
        days: Math.floor(difference / (1000 * 60 * 60 * 24)),
        hours: Math.floor((difference % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((difference % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((difference % (1000 * 60)) / 1000)
      });
    } else {
      setTimeLeft({});
      // Refresh data if countdown has expired
      fetchCountdownData();
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Countdown</h3>
        </div>
        <div className="text-center p-4">
          <div className="loading">Loading countdown...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Countdown</h3>
        </div>
        <div className="alert alert-error">
          {error}
        </div>
      </div>
    );
  }

  if (!countdownData?.countdown) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Countdown</h3>
        </div>
        <div className="text-center p-4">
          <div style={{ color: 'var(--text-light)', fontSize: '1.1rem' }}>
            No upcoming approved leave found
          </div>
          <p style={{ color: 'var(--text-light)', fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Apply for leave to see your countdown here
          </p>
        </div>
      </div>
    );
  }

  const { countdown } = countdownData;
  const isCurrentLeave = countdown.type === 'current_leave';

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">
          {isCurrentLeave ? 'Current Leave Ending' : 'Next Leave Starting'}
        </h3>
      </div>

      <div style={{ padding: '1.5rem' }}>
        {/* Leave Information */}
        <div style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ 
            fontSize: '1.2rem', 
            color: 'var(--primary-blue)', 
            marginBottom: '0.5rem' 
          }}>
            {countdown.leave.leave_type_name}
          </h4>
          <p style={{ 
            color: 'var(--text-light)', 
            fontSize: '0.9rem',
            marginBottom: '0.25rem'
          }}>
            {formatDate(countdown.leave.start_date)} - {formatDate(countdown.leave.end_date)}
          </p>
          <p style={{ 
            color: 'var(--text-light)', 
            fontSize: '0.9rem' 
          }}>
            Duration: {countdown.leave.days_requested} days
          </p>
        </div>

        {/* Countdown Display */}
        {Object.keys(timeLeft).length > 0 ? (
          <div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: '1rem',
              marginBottom: '1rem'
            }}>
              {[
                { label: 'Days', value: timeLeft.days },
                { label: 'Hours', value: timeLeft.hours },
                { label: 'Minutes', value: timeLeft.minutes },
                { label: 'Seconds', value: timeLeft.seconds }
              ].map(({ label, value }) => (
                <div
                  key={label}
                  style={{
                    textAlign: 'center',
                    padding: '1rem',
                    backgroundColor: 'var(--background-light)',
                    borderRadius: '8px',
                    border: '2px solid var(--primary-blue)'
                  }}
                >
                  <div style={{
                    fontSize: '2rem',
                    fontWeight: '700',
                    color: 'var(--primary-blue)',
                    lineHeight: '1'
                  }}>
                    {value || 0}
                  </div>
                  <div style={{
                    fontSize: '0.875rem',
                    color: 'var(--text-light)',
                    marginTop: '0.25rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px'
                  }}>
                    {label}
                  </div>
                </div>
              ))}
            </div>

            <div style={{
              textAlign: 'center',
              padding: '1rem',
              backgroundColor: isCurrentLeave ? 'rgba(255, 193, 7, 0.1)' : 'rgba(0, 51, 102, 0.1)',
              borderRadius: '8px',
              border: `2px solid ${isCurrentLeave ? 'var(--warning)' : 'var(--primary-blue)'}`
            }}>
              <div style={{
                fontSize: '1.1rem',
                fontWeight: '600',
                color: isCurrentLeave ? 'var(--warning)' : 'var(--primary-blue)',
                marginBottom: '0.25rem'
              }}>
                {isCurrentLeave ? 'Leave ends in:' : 'Leave starts in:'}
              </div>
              <div style={{
                fontSize: '1.5rem',
                fontWeight: '700',
                color: isCurrentLeave ? 'var(--warning)' : 'var(--primary-blue)'
              }}>
                {timeLeft.days} days, {timeLeft.hours} hours, {timeLeft.minutes} minutes
              </div>
            </div>
          </div>
        ) : (
          <div style={{
            textAlign: 'center',
            padding: '2rem',
            backgroundColor: 'var(--background-light)',
            borderRadius: '8px'
          }}>
            <div style={{
              fontSize: '3rem',
              marginBottom: '1rem'
            }}>
              {isCurrentLeave ? '🏖️' : '🎉'}
            </div>
            <div style={{
              fontSize: '1.2rem',
              fontWeight: '600',
              color: 'var(--primary-blue)',
              marginBottom: '0.5rem'
            }}>
              {isCurrentLeave ? 'Your leave has ended!' : 'Your leave starts today!'}
            </div>
            <div style={{
              color: 'var(--text-light)',
              fontSize: '0.9rem'
            }}>
              {isCurrentLeave ? 'Welcome back to work!' : 'Enjoy your time off!'}
            </div>
          </div>
        )}

        {/* Additional Information */}
        {countdown.leave.person_handling_duties_name && (
          <div style={{
            marginTop: '1rem',
            padding: '0.75rem',
            backgroundColor: 'var(--background-light)',
            borderRadius: '4px',
            fontSize: '0.9rem'
          }}>
            <strong>Duties handled by:</strong> {countdown.leave.person_handling_duties_name}
          </div>
        )}
      </div>
    </div>
  );
};

export default Countdown;

