import React, { useEffect, useState } from 'react';
import Select from 'react-select';
import api from '../../services/authService'; // or your axios instance

const PersonHandlingDropdown = ({ role, value, onChange }) => {
  const [options, setOptions] = useState([]);

  useEffect(() => {
    const fetchUsers = async () => {
      const endpoint = role === 'hod' ? '/api/dashboard/available-hods' : '/api/dashboard/available-staff';
      const res = await api.get(endpoint);
      setOptions(
        res.data.map(user => ({
          value: user.id,
          label: `${user.first_name} ${user.last_name} (${user.role})`
        }))
      );
    };
    fetchUsers();
  }, [role]);

  return (
    <Select
      options={options}
      value={options.find(opt => opt.value === value)}
      onChange={opt => onChange(opt ? opt.value : '')}
      placeholder={`Select ${role === 'hod' ? 'HOD' : 'Staff'} to handle duties`}
      isClearable
      isSearchable
    />
  );
};

export default PersonHandlingDropdown;