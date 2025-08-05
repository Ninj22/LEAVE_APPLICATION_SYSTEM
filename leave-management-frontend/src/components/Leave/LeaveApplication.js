import React, { useState, useEffect } from 'react';
import { leaveService } from '../../services/leaveService';
import PersonHandlingDropdown from './PersonHandlingDropdown';

const LeaveApplication = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    leave_type_id: '',
    start_date: '',
    end_date: '',
    last_leave_from: '',
    last_leave_to: '',
    contact_info: '',
    salary_payment_preference: 'bank_account',
    salary_payment_address: '',
    permission_note_country: '',
    person_handling_duties_id: ''
  });

  const [leaveTypes, setLeaveTypes] = useState([]);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState({});
  const [calculatedDays, setCalculatedDays] = useState(0);

  useEffect(() => {
    fetchLeaveTypes();
  }, []);

  useEffect(() => {
    if (formData.start_date && formData.end_date) {
      calculateDays();
      fetchAvailableUsers();
    }
  }, [formData.start_date, formData.end_date]);

  const fetchLeaveTypes = async () => {
    try {
      const data = await leaveService.getLeaveTypes();
      setLeaveTypes(data.leave_types);
    } catch (error) {
      setError('Failed to load leave types');
    }
  };

  const fetchAvailableUsers = async () => {
    if (!formData.start_date || !formData.end_date) return;

    try {
      const data = await leaveService.getAvailableUsers(formData.start_date, formData.end_date);
      setAvailableUsers(data.users);
    } catch (error) {
      console.error('Failed to load available users:', error);
    }
  };

  const calculateDays = () => {
    if (!formData.start_date || !formData.end_date) {
      setCalculatedDays(0);
      return;
    }

    const start = new Date(formData.start_date);
    const end = new Date(formData.end_date);
    
    if (start > end) {
      setCalculatedDays(0);
      return;
    }

    // Calculate working days (excluding weekends)
    let workingDays = 0;
    const currentDate = new Date(start);
    
    while (currentDate <= end) {
      const dayOfWeek = currentDate.getDay();
      if (dayOfWeek !== 0 && dayOfWeek !== 6) { // Not Sunday (0) or Saturday (6)
        workingDays++;
      }
      currentDate.setDate(currentDate.getDate() + 1);
    }

    setCalculatedDays(workingDays);
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.leave_type_id) {
      errors.leave_type_id = 'Please select a leave type';
    }

    if (!formData.start_date) {
      errors.start_date = 'Start date is required';
    }

    if (!formData.end_date) {
      errors.end_date = 'End date is required';
    }

    if (formData.start_date && formData.end_date && formData.leave_type_id) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      

      if (start < today) {
        errors.start_date = 'Start date cannot be in the past';
      }

      if (start > end) {
        errors.end_date = 'End date must be after start date';
      }

      const selectedLeaveType = leaveTypes.find(type => type.id === parseInt(formData.leave_type_id));
      if (selectedLeaveType && calculatedDays > selectedLeaveType.max_days) {
        errors.calculatedDays = `Exceeds maximum allowed days (${selectedLeaveType.max_days})`;
      }
    }

    if (!formData.contact_info.trim()) {
      errors.contact_info = 'Contact information is required';
    }

    if (formData.salary_payment_preference === 'address' && !formData.salary_payment_address.trim()) {
      errors.salary_payment_address = 'Payment address is required when not using bank account';
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
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors);
      return;
    }

    setLoading(true);
    setError('');
    setValidationErrors({});

    try {
      const response = await leaveService.applyLeave(formData);
      
      // Reset form
      setFormData({
        leave_type_id: '',
        start_date: '',
        end_date: '',
        last_leave_from: '',
        last_leave_to: '',
        contact_info: '',
        salary_payment_preference: 'bank_account',
        salary_payment_address: '',
        permission_note_country: '',
        person_handling_duties_id: ''
      });
      setCalculatedDays(0);
      setAvailableUsers([]);

      if (onSuccess) {
        onSuccess(response);
      }

    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const selectedLeaveType = leaveTypes.find(type => type.id === parseInt(formData.leave_type_id));

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Apply for Leave</h3>
      </div>

      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="row">
          <div className="col-12 col-md-6">
            <div className="form-group">
              <label htmlFor="leave_type_id" className="form-label">
                Leave Type *
              </label>
              <select
                id="leave_type_id"
                name="leave_type_id"
                className="form-select"
                value={formData.leave_type_id}
                onChange={handleChange}
                required
              >
                <option value="">Select leave type</option>
                {leaveTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.name} (Max: {type.max_days} days)
                  </option>
                ))}
              </select>
              {validationErrors.leave_type_id && (
                <div className="form-error">{validationErrors.leave_type_id}</div>
              )}
            </div>
          </div>

          <div className="col-12 col-md-6">
            <div className="form-group">
              <label className="form-label">Calculated Days</label>
              <div style={{
                padding: '0.75rem',
                backgroundColor: 'var(--background-light)',
                border: '2px solid var(--border-light)',
                borderRadius: '4px',
                fontSize: '1rem',
                fontWeight: '600',
                color: 'var(--primary-blue)'
              }}>
                {calculatedDays} working days
              </div>
              {validationErrors.calculatedDays && (
                <div className="form-error">
                  {validationErrors.calculatedDays}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-12 col-md-6">
            <div className="form-group">
              <label htmlFor="start_date" className="form-label">
                Start Date *
              </label>
              <input
                type="date"
                id="start_date"
                name="start_date"
                className="form-input"
                value={formData.start_date}
                onChange={handleChange}
                min={new Date().toISOString().split('T')[0]}
                required
              />
              {validationErrors.start_date && (
                <div className="form-error">{validationErrors.start_date}</div>
              )}
            </div>
          </div>

          <div className="col-12 col-md-6">
            <div className="form-group">
              <label htmlFor="end_date" className="form-label">
                End Date *
              </label>
              <input
                type="date"
                id="end_date"
                name="end_date"
                className="form-input"
                value={formData.end_date}
                onChange={handleChange}
                min={formData.start_date || new Date().toISOString().split('T')[0]}
                required
              />
              {validationErrors.end_date && (
                <div className="form-error">{validationErrors.end_date}</div>
              )}
            </div>
          </div>
        </div>

        <div className="row">
          <div className="col-12 col-md-6">
            <div className="form-group">
              <label htmlFor="last_leave_from" className="form-label">
                Last Leave From
              </label>
              <input
                type="date"
                id="last_leave_from"
                name="last_leave_from"
                className="form-input"
                value={formData.last_leave_from}
                onChange={handleChange}
              />
            </div>
          </div>

          <div className="col-12 col-md-6">
            <div className="form-group">
              <label htmlFor="last_leave_to" className="form-label">
                Last Leave To
              </label>
              <input
                type="date"
                id="last_leave_to"
                name="last_leave_to"
                className="form-input"
                value={formData.last_leave_to}
                onChange={handleChange}
              />
            </div>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="contact_info" className="form-label">
            Contact Information While on Leave *
          </label>
          <textarea
            id="contact_info"
            name="contact_info"
            className="form-textarea"
            value={formData.contact_info}
            onChange={handleChange}
            placeholder="Enter your contact details (phone, address, etc.)"
            required
          />
          {validationErrors.contact_info && (
            <div className="form-error">{validationErrors.contact_info}</div>
          )}
        </div>

        <div className="form-group">
          <label className="form-label">Salary Payment Preference *</label>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                name="salary_payment_preference"
                value="bank_account"
                checked={formData.salary_payment_preference === 'bank_account'}
                onChange={handleChange}
              />
              Continue to bank account
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="radio"
                name="salary_payment_preference"
                value="address"
                checked={formData.salary_payment_preference === 'address'}
                onChange={handleChange}
              />
              Pay at different address
            </label>
          </div>
          
          {formData.salary_payment_preference === 'address' && (
            <textarea
              name="salary_payment_address"
              className="form-textarea"
              value={formData.salary_payment_address}
              onChange={handleChange}
              placeholder="Enter payment address"
              style={{ marginTop: '0.5rem' }}
            />
          )}
          {validationErrors.salary_payment_address && (
            <div className="form-error">{validationErrors.salary_payment_address}</div>
          )}
        </div>

        <div className="form-group">
          <label htmlFor="permission_note_country" className="form-label">
            Permission Note for Leaving Country
          </label>
          <textarea
            id="permission_note_country"
            name="permission_note_country"
            className="form-textarea"
            value={formData.permission_note_country}
            onChange={handleChange}
            placeholder="If you plan to leave Kenya during your leave, please provide details"
          />
          <small style={{ color: 'var(--text-light)', fontSize: '0.875rem' }}>
            Required if you plan to spend leave outside Kenya (as per HR policies)
          </small>
        </div>

<div className="form-group">
  <label htmlFor="person_handling_duties_id" className="form-label">
    Person Handling Duties
  </label>
  <select
    id="person_handling_duties_id"
    name="person_handling_duties_id"
    className="form-select"
    value={formData.person_handling_duties_id}
    onChange={handleChange}
  >
    <option value="">Select person to handle duties</option>
    {availableUsers.map(user => (
      <option 
        key={user.id} 
        value={user.id}
        disabled={!user.available}
        style={{ 
          opacity: user.available ? 1 : 0.5,
          fontStyle: user.available ? 'normal' : 'italic'
        }}
      >
        {user.first_name} {user.last_name} ({user.role})
        {!user.available ? ' - Unavailable' : ''}
      </option>
    ))}
  </select>
  <small style={{ color: 'var(--text-light)', fontSize: '0.875rem' }}>
    Only available staff members are shown. Unavailable staff are faded out.
  </small>
</div>

        <div className="btn-group btn-group-end">
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || (selectedLeaveType && calculatedDays > selectedLeaveType.max_days)}
          >
            {loading ? 'Submitting...' : 'Submit Application'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default LeaveApplication;

