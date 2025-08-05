import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Login = () => {
  const [formData, setFormData] = useState({
    employeeNumber: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const { login, user, error, clearError } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  useEffect(() => {
    clearError();
  }, [clearError]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    clearError();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await login(formData.employeeNumber, formData.password);
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    } finally {
      setIsLoading(false);
    }
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
                <h3 className="card-title text-center">Login</h3>
              </div>

              {error && (
                <div className="alert alert-error">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div className="form-group">
                  <label htmlFor="employeeNumber" className="form-label">
                    Employee Number
                  </label>
                  <input
                    type="text"
                    id="employeeNumber"
                    name="employeeNumber"
                    className="form-input"
                    value={formData.employeeNumber}
                    onChange={handleChange}
                    placeholder="Enter your employee number"
                    required
                  />
                  <small className="form-help" style={{ color: 'var(--text-light)', fontSize: '0.875rem' }}>
                  </small>
                </div>

                <div className="form-group">
                  <label htmlFor="password" className="form-label">
                    Password
                  </label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    className="form-input"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Enter your password"
                    required
                  />
                </div>

                <div className="form-group">
                  <button
                    type="submit"
                    className="btn btn-primary w-full"
                    disabled={isLoading}
                  >
                    {isLoading ? 'Signing In...' : 'Sign In'}
                  </button>
                </div>

                <div className="text-center">
                  <Link 
                    to="/forgot-password" 
                    style={{ color: 'var(--primary-blue)', textDecoration: 'none' }}
                  >
                    Forgot Password?
                  </Link>
                </div>

                <hr style={{ margin: '1.5rem 0', border: 'none', borderTop: '1px solid var(--border-light)' }} />

                <div className="text-center">
                  <p style={{ color: 'var(--text-light)', marginBottom: '0.5rem' }}>
                    Don't have an account?
                  </p>
                  <Link 
                    to="/signup" 
                    className="btn btn-outline w-full"
                  >
                    Create Account
                  </Link>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;

