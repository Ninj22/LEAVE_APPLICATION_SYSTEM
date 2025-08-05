import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [step, setStep] = useState(1); // 1: email, 2: reset
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [validationError, setValidationError] = useState('');
  const { forgotPassword, resetPassword, error, clearError } = useAuth();

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setValidationError('');
    clearError();

    try {
      await forgotPassword(email);
      setMessage('If the email exists, a reset token has been sent to your email.');
      setStep(2);
    } catch (error) {
      console.error('Forgot password failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSubmit = async (e) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setValidationError('Passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setValidationError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);
    setValidationError('');
    clearError();

    try {
      await resetPassword(token, newPassword);
      setMessage('Password reset successfully! You can now log in with your new password.');
      setStep(3);
    } catch (error) {
      console.error('Reset password failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (setter) => (e) => {
    setter(e.target.value);
    setValidationError('');
    clearError();
  };

  return (
    <div className="min-h-screen d-flex align-center justify-center" style={{ backgroundColor: 'var(--background-light)' }}>
      <div className="container">
        <div className="row justify-center">
          <div className="col-12 col-md-6 col-lg-4">
            <div className="card fade-in">
              <div className="text-center mb-4">
                <h1 style={{ color: 'var(--primary-blue)', fontSize: '2rem', marginBottom: '0.5rem' }}>
                  Ministry of ICT
                </h1>
                <h2 style={{ color: 'var(--text-light)', fontSize: '1.2rem', fontWeight: 'normal' }}>
                  Leave Management System
                </h2>
              </div>

              <div className="card-header">
                <h3 className="card-title text-center">
                  {step === 1 ? 'Forgot Password' : step === 2 ? 'Reset Password' : 'Password Reset Complete'}
                </h3>
              </div>

              {error && (
                <div className="alert alert-error">
                  {error}
                </div>
              )}

              {validationError && (
                <div className="alert alert-error">
                  {validationError}
                </div>
              )}

              {message && (
                <div className="alert alert-success">
                  {message}
                </div>
              )}

              {step === 1 && (
                <form onSubmit={handleEmailSubmit}>
                  <div className="form-group">
                    <label htmlFor="email" className="form-label">
                      Email Address
                    </label>
                    <input
                      type="email"
                      id="email"
                      className="form-input"
                      value={email}
                      onChange={handleChange(setEmail)}
                      placeholder="Enter your email address"
                      required
                    />
                    <small style={{ color: 'var(--text-light)', fontSize: '0.875rem' }}>
                      Enter the email address associated with your account
                    </small>
                  </div>

                  <div className="form-group">
                    <button
                      type="submit"
                      className="btn btn-primary w-full"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Sending...' : 'Send Reset Token'}
                    </button>
                  </div>

                  <div className="text-center">
                    <Link 
                      to="/login" 
                      style={{ color: 'var(--primary-blue)', textDecoration: 'none' }}
                    >
                      Back to Login
                    </Link>
                  </div>
                </form>
              )}

              {step === 2 && (
                <form onSubmit={handleResetSubmit}>
                  <div className="form-group">
                    <label htmlFor="token" className="form-label">
                      Reset Token
                    </label>
                    <input
                      type="text"
                      id="token"
                      className="form-input"
                      value={token}
                      onChange={handleChange(setToken)}
                      placeholder="Enter the reset token from your email"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="newPassword" className="form-label">
                      New Password
                    </label>
                    <input
                      type="password"
                      id="newPassword"
                      className="form-input"
                      value={newPassword}
                      onChange={handleChange(setNewPassword)}
                      placeholder="Enter new password"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="confirmPassword" className="form-label">
                      Confirm New Password
                    </label>
                    <input
                      type="password"
                      id="confirmPassword"
                      className="form-input"
                      value={confirmPassword}
                      onChange={handleChange(setConfirmPassword)}
                      placeholder="Confirm new password"
                      required
                    />
                  </div>

                  <div className="form-group">
                    <button
                      type="submit"
                      className="btn btn-primary w-full"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Resetting...' : 'Reset Password'}
                    </button>
                  </div>

                  <div className="text-center">
                    <button
                      type="button"
                      onClick={() => setStep(1)}
                      style={{ 
                        background: 'none', 
                        border: 'none', 
                        color: 'var(--primary-blue)', 
                        textDecoration: 'underline',
                        cursor: 'pointer'
                      }}
                    >
                      Back to Email Step
                    </button>
                  </div>
                </form>
              )}

              {step === 3 && (
                <div className="text-center">
                  <div style={{ color: 'var(--success)', fontSize: '3rem', marginBottom: '1rem' }}>
                    ✓
                  </div>
                  <p style={{ color: 'var(--text-dark)', marginBottom: '2rem' }}>
                    Your password has been reset successfully!
                  </p>
                  <Link 
                    to="/login" 
                    className="btn btn-primary w-full"
                  >
                    Go to Login
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;

