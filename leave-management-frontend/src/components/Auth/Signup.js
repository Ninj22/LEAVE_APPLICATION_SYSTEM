import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Signup = () => {
  const [formData, setFormData] = useState({
    employeeNumber: '',
    email: '',
    phoneNumber: '',
    firstName: '',
    lastName: '',
    password: '',
    confirmPassword: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const { signup, user, error, clearError } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      navigate('/dashboard');
    }
  }, [user, navigate]);

  useEffect(() => {
    clearError();
  }, [clearError]);

  const validateForm = () => {
    const errors = {};

    // Employee Number validation
    if (!formData.employeeNumber) {
      errors.employeeNumber = 'Employee number is required';
    } else if (!/^\d{4,6}$/.test(formData.employeeNumber)) {
      errors.employeeNumber = 'Employee number must be 4-6 digits';
    }

    // Email validation
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    // Phone validation
    if (!formData.phoneNumber) {
      errors.phoneNumber = 'Phone number is required';
    } else if (!/^\+?[1-9]\d{1,14}$/.test(formData.phoneNumber)) {
      errors.phoneNumber = 'Please enter a valid phone number';
    }

    // Name validation
    if (!formData.firstName.trim()) {
      errors.firstName = 'First name is required';
    }
    if (!formData.lastName.trim()) {
      errors.lastName = 'Last name is required';
    }

    // Password validation
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    return errors;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    clearError();
    setSuccessMessage('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setIsLoading(true);
    setValidationErrors({});

    try {
      const signupData = {
        employee_number: formData.employeeNumber,
        email: formData.email,
        phone_number: formData.phoneNumber,
        first_name: formData.firstName,
        last_name: formData.lastName,
        password: formData.password,
      };

      await signup(signupData);
      setSuccessMessage('Account created successfully! You can now log in.');
      
      // Reset form
      setFormData({
        employeeNumber: '',
        email: '',
        phoneNumber: '',
        firstName: '',
        lastName: '',
        password: '',
        confirmPassword: '',
      });

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);

    } catch (error) {
      console.error('Signup failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getRoleFromEmployeeNumber = (empNum) => {
    if (!empNum) return '';
    const length = empNum.length;
    if (length === 4) return 'Staff';
    if (length === 5) return 'Head of Department';
    if (length === 6) return 'Principal Secretary';
    return '';
  };

  return (
    <div className="min-h-screen d-flex align-center justify-center" style={{ backgroundColor: 'var(--background-light)', padding: '2rem 0' }}>
      <div className="container">
        <div className="row justify-center">
          <div className="col-12 col-md-8 col-lg-6">
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
                <h3 className="card-title text-center">Create Account</h3>
              </div>

              {error && (
                <div className="alert alert-error">
                  {error}
                </div>
              )}

              {successMessage && (
                <div className="alert alert-success">
                  {successMessage}
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div className="row">
                  <div className="col-12 col-md-6">
                    <div className="form-group">
                      <label htmlFor="employeeNumber" className="form-label">
                        Employee Number *
                      </label>
                      <input
                        type="text"
                        id="employeeNumber"
                        name="employeeNumber"
                        className="form-input"
                        value={formData.employeeNumber}
                        onChange={handleChange}
                        placeholder="Enter employee number"
                        required
                      />
                      {validationErrors.employeeNumber && (
                        <div className="form-error">{validationErrors.employeeNumber}</div>
                      )}
                      {formData.employeeNumber && (
                        <div className="form-success">
                          Role: {getRoleFromEmployeeNumber(formData.employeeNumber)}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="col-12 col-md-6">
                    <div className="form-group">
                      <label htmlFor="email" className="form-label">
                        Email Address *
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        className="form-input"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="Enter email address"
                        required
                      />
                      {validationErrors.email && (
                        <div className="form-error">{validationErrors.email}</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="row">
                  <div className="col-12 col-md-6">
                    <div className="form-group">
                      <label htmlFor="firstName" className="form-label">
                        First Name *
                      </label>
                      <input
                        type="text"
                        id="firstName"
                        name="firstName"
                        className="form-input"
                        value={formData.firstName}
                        onChange={handleChange}
                        placeholder="Enter first name"
                        required
                      />
                      {validationErrors.firstName && (
                        <div className="form-error">{validationErrors.firstName}</div>
                      )}
                    </div>
                  </div>

                  <div className="col-12 col-md-6">
                    <div className="form-group">
                      <label htmlFor="lastName" className="form-label">
                        Last Name *
                      </label>
                      <input
                        type="text"
                        id="lastName"
                        name="lastName"
                        className="form-input"
                        value={formData.lastName}
                        onChange={handleChange}
                        placeholder="Enter last name"
                        required
                      />
                      {validationErrors.lastName && (
                        <div className="form-error">{validationErrors.lastName}</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="phoneNumber" className="form-label">
                    Phone Number *
                  </label>
                  <input
                    type="tel"
                    id="phoneNumber"
                    name="phoneNumber"
                    className="form-input"
                    value={formData.phoneNumber}
                    onChange={handleChange}
                    placeholder="Enter phone number (e.g., +254712345678)"
                    required
                  />
                  {validationErrors.phoneNumber && (
                    <div className="form-error">{validationErrors.phoneNumber}</div>
                  )}
                </div>

                <div className="row">
                  <div className="col-12 col-md-6">
                    <div className="form-group">
                      <label htmlFor="password" className="form-label">
                        Password *
                      </label>
                      <input
                        type="password"
                        id="password"
                        name="password"
                        className="form-input"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="Enter password"
                        required
                      />
                      {validationErrors.password && (
                        <div className="form-error">{validationErrors.password}</div>
                      )}
                    </div>
                  </div>

                  <div className="col-12 col-md-6">
                    <div className="form-group">
                      <label htmlFor="confirmPassword" className="form-label">
                        Confirm Password *
                      </label>
                      <input
                        type="password"
                        id="confirmPassword"
                        name="confirmPassword"
                        className="form-input"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        placeholder="Confirm password"
                        required
                      />
                      {validationErrors.confirmPassword && (
                        <div className="form-error">{validationErrors.confirmPassword}</div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <button
                    type="submit"
                    className="btn btn-primary w-full"
                    disabled={isLoading}
                  >
                    {isLoading ? 'Creating Account...' : 'Create Account'}
                  </button>
                </div>

                <div className="text-center">
                  <p style={{ color: 'var(--text-light)', marginBottom: '0.5rem' }}>
                    Already have an account?
                  </p>
                  <Link 
                    to="/login" 
                    className="btn btn-outline w-full"
                  >
                    Sign In
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

export default Signup;

