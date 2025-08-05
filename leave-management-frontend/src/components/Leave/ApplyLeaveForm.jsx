import React, { useState } from 'react';

function ApplyLeave() {
  const [formData, setFormData] = useState({
    leave_type: '',
    start_date: '',
    end_date: '',
    reason: '',
    contact_info: '',
    salary_payment_preference: 'bank_account', // default
    salary_payment_address: '',
    permission_note_country: '',
    person_handling_duties_id: ''
  });

  const token = localStorage.getItem('token');

  const handleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log("Submitting leave data:", formData);

    try {
      const res = await fetch('/api/leaves/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      const data = await res.json();
      
      if (res.status === 201) {
        alert('Leave application submitted successfully!');
      } else {
        alert(`Error: ${data.error || data.message}`);
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Something went wrong.');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Leave Type:
        <input
          type="text"
          name="leave_type"
          value={formData.leave_type}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Start Date:
        <input
          type="date"
          name="start_date"
          value={formData.start_date}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        End Date:
        <input
          type="date"
          name="end_date"
          value={formData.end_date}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Reason:
        <textarea
          name="reason"
          value={formData.reason}
          onChange={handleChange}
          required
        />
      </label>

      <label>
        Contact Info:
        <input
          type="text"
          name="contact_info"
          value={formData.contact_info}
          onChange={handleChange}
        />
      </label>

      <label>
        Salary Payment Preference:
        <select
          name="salary_payment_preference"
          value={formData.salary_payment_preference}
          onChange={handleChange}
        >
          <option value="bank_account">Bank Account</option>
          <option value="mobile_money">Mobile Money</option>
        </select>
      </label>

      <label>
        Salary Payment Address:
        <input
          type="text"
          name="salary_payment_address"
          value={formData.salary_payment_address}
          onChange={handleChange}
        />
      </label>

      <label>
        Permission Note Country:
        <input
          type="text"
          name="permission_note_country"
          value={formData.permission_note_country}
          onChange={handleChange}
        />
      </label>

      <label>
        Person Handling Duties (Employee ID):
        <input
          type="text"
          name="person_handling_duties_id"
          value={formData.person_handling_duties_id}
          onChange={handleChange}
        />
      </label>

      <button type="submit">Apply for Leave</button>
    </form>
  );
}

export default ApplyLeave;
