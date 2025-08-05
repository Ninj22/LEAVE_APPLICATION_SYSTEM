import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const Navigation = () => {
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
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

  return (
    <nav style={{
      backgroundColor: 'var(--primary-blue)',
      color: 'var(--white)',
      padding: '1rem 0',
      boxShadow: '0 2px 4px var(--shadow)'
    }}>
      <div className="container">
        <div className="d-flex justify-between align-center">
          <div>
            <h1 style={{ 
              fontSize: '1.5rem', 
              margin: 0, 
              fontWeight: '600' 
            }}>
              Ministry of ICT - Leave Management
            </h1>
            {user && (
              <p style={{ 
                margin: 0, 
                fontSize: '0.9rem', 
                opacity: 0.9 
              }}>
                Welcome, {user.first_name} {user.last_name} ({getRoleDisplayName(user.role)})
              </p>
            )}
          </div>
          
          {user && (
            <div className="d-flex align-center" style={{ gap: '1rem' }}>
              <span style={{ fontSize: '0.9rem', opacity: 0.9 }}>
                Employee #: {user.employee_number}
              </span>
              <button
                onClick={handleLogout}
                className="btn btn-outline"
                style={{
                  borderColor: 'var(--white)',
                  color: 'var(--white)',
                  padding: '0.5rem 1rem',
                  fontSize: '0.9rem'
                }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;

