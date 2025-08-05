import React, { useState, useEffect } from 'react';
import { dashboardService } from '../../services/leaveService';

const Calendar = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarData, setCalendarData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchCalendarData();
  }, [currentDate]);

  const fetchCalendarData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getCalendarData(
        currentDate.getFullYear(),
        currentDate.getMonth() + 1
      );
      setCalendarData(data);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const isLeaveDay = (day) => {
    if (!calendarData?.leaves) return false;
    
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    
    return calendarData.leaves.some(leave => {
      const startDate = new Date(leave.calendar_start);
      const endDate = new Date(leave.calendar_end);
      const checkDate = new Date(dateStr);
      
      return checkDate >= startDate && checkDate <= endDate;
    });
  };

  const getLeaveForDay = (day) => {
    if (!calendarData?.leaves) return null;
    
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    
    return calendarData.leaves.find(leave => {
      const startDate = new Date(leave.calendar_start);
      const endDate = new Date(leave.calendar_end);
      const checkDate = new Date(dateStr);
      
      return checkDate >= startDate && checkDate <= endDate;
    });
  };

  const navigateMonth = (direction) => {
    setCurrentDate(prev => {
      const newDate = new Date(prev);
      newDate.setMonth(prev.getMonth() + direction);
      return newDate;
    });
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  if (loading) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Calendar</h3>
        </div>
        <div className="text-center p-4">
          <div className="loading">Loading calendar...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Leave Calendar</h3>
        </div>
        <div className="alert alert-error">
          {error}
        </div>
      </div>
    );
  }

  const daysInMonth = getDaysInMonth(currentDate);
  const firstDay = getFirstDayOfMonth(currentDate);
  const today = new Date();
  const isCurrentMonth = today.getFullYear() === currentDate.getFullYear() && 
                         today.getMonth() === currentDate.getMonth();

  return (
    <div className="card">
      <div className="card-header">
        <div className="d-flex justify-between align-center">
          <h3 className="card-title">Leave Calendar</h3>
          <div className="d-flex align-center" style={{ gap: '1rem' }}>
            <button
              onClick={() => navigateMonth(-1)}
              className="btn btn-sm btn-outline"
              style={{ padding: '0.25rem 0.5rem' }}
            >
              ‹
            </button>
            <span style={{ fontWeight: '600', minWidth: '150px', textAlign: 'center' }}>
              {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
            </span>
            <button
              onClick={() => navigateMonth(1)}
              className="btn btn-sm btn-outline"
              style={{ padding: '0.25rem 0.5rem' }}
            >
              ›
            </button>
          </div>
        </div>
      </div>

      <div style={{ padding: '1rem' }}>
        {/* Calendar Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(7, 1fr)',
          gap: '1px',
          backgroundColor: 'var(--border-light)',
          border: '1px solid var(--border-light)'
        }}>
          {/* Day Headers */}
          {dayNames.map(day => (
            <div
              key={day}
              style={{
                backgroundColor: 'var(--primary-blue)',
                color: 'var(--white)',
                padding: '0.5rem',
                textAlign: 'center',
                fontWeight: '600',
                fontSize: '0.875rem'
              }}
            >
              {day}
            </div>
          ))}

          {/* Empty cells for days before month starts */}
          {Array.from({ length: firstDay }, (_, i) => (
            <div
              key={`empty-${i}`}
              style={{
                backgroundColor: 'var(--background-light)',
                height: '60px'
              }}
            />
          ))}

          {/* Days of the month */}
          {Array.from({ length: daysInMonth }, (_, i) => {
            const day = i + 1;
            const isToday = isCurrentMonth && today.getDate() === day;
            const isLeave = isLeaveDay(day);
            const leave = getLeaveForDay(day);

            return (
              <div
                key={day}
                style={{
                  backgroundColor: isLeave ? 'rgba(255, 215, 0, 0.2)' : 'var(--white)',
                  border: isToday ? '2px solid var(--primary-blue)' : 'none',
                  height: '60px',
                  padding: '0.25rem',
                  position: 'relative',
                  cursor: isLeave ? 'pointer' : 'default'
                }}
                title={isLeave ? `${leave.leave_type_name}: ${leave.start_date} to ${leave.end_date}` : ''}
              >
                <div style={{
                  fontWeight: isToday ? '600' : 'normal',
                  color: isToday ? 'var(--primary-blue)' : 'var(--text-dark)',
                  fontSize: '0.875rem'
                }}>
                  {day}
                </div>
                {isLeave && (
                  <div style={{
                    position: 'absolute',
                    bottom: '2px',
                    left: '2px',
                    right: '2px',
                    backgroundColor: 'var(--accent-gold)',
                    color: 'var(--text-dark)',
                    fontSize: '0.625rem',
                    padding: '1px 2px',
                    borderRadius: '2px',
                    textAlign: 'center',
                    fontWeight: '600',
                    overflow: 'hidden',
                    whiteSpace: 'nowrap',
                    textOverflow: 'ellipsis'
                  }}>
                    {leave.leave_type_name.split(' ')[0]}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
          <div className="d-flex align-center" style={{ gap: '0.5rem' }}>
            <div style={{
              width: '16px',
              height: '16px',
              backgroundColor: 'rgba(255, 215, 0, 0.2)',
              border: '1px solid var(--accent-gold)',
              borderRadius: '2px'
            }} />
            <span>Leave Days</span>
          </div>
          <div className="d-flex align-center" style={{ gap: '0.5rem' }}>
            <div style={{
              width: '16px',
              height: '16px',
              border: '2px solid var(--primary-blue)',
              borderRadius: '2px'
            }} />
            <span>Today</span>
          </div>
        </div>

        {/* Leave Summary */}
        {calendarData?.leaves && calendarData.leaves.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <h4 style={{ fontSize: '1rem', marginBottom: '0.5rem', color: 'var(--primary-blue)' }}>
              Leave Days This Month
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {calendarData.leaves.map((leave, index) => (
                <div
                  key={index}
                  style={{
                    padding: '0.5rem',
                    backgroundColor: 'var(--background-light)',
                    borderRadius: '4px',
                    fontSize: '0.875rem'
                  }}
                >
                  <div style={{ fontWeight: '600', color: 'var(--primary-blue)' }}>
                    {leave.leave_type_name}
                  </div>
                  <div style={{ color: 'var(--text-light)' }}>
                    {new Date(leave.start_date).toLocaleDateString()} - {new Date(leave.end_date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Calendar;

