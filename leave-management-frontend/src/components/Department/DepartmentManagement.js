import React, { useState, useEffect } from 'react';
import { departmentService } from '../../services/leaveService';
import { userService } from '../../services/userService'; // Assuming you have a userService to get all HODs
import { someFunction } from '../../services/userService';

const DepartmentManagement = () => {
  const [departments, setDepartments] = useState([]);
  const [hodsWithoutDepartment, setHodsWithoutDepartment] = useState([]);
  const [newDepartmentName, setNewDepartmentName] = useState('');
  const [selectedHodId, setSelectedHodId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [editDepartmentId, setEditDepartmentId] = useState(null);
  const [editDepartmentName, setEditDepartmentName] = useState('');
  const [editHodId, setEditHodId] = useState('');

  useEffect(() => {
    fetchDepartments();
    fetchHODsWithoutDepartment();
  }, []);

  const fetchDepartments = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await departmentService.getDepartments();
      setDepartments(data.departments);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchHODsWithoutDepartment = async () => {
    try {
      const data = await departmentService.getHODsWithoutDepartment();
      setHodsWithoutDepartment(data.hods);
    } catch (error) {
      console.error('Failed to fetch HODs without department:', error);
    }
  };

  const handleCreateDepartment = async (e) => {
    e.preventDefault();
    if (!newDepartmentName.trim()) {
      setError('Department name cannot be empty');
      return;
    }
    try {
      setLoading(true);
      setError('');
      await departmentService.createDepartment({
        name: newDepartmentName,
        hod_id: selectedHodId || null,
      });
      setNewDepartmentName('');
      setSelectedHodId('');
      fetchDepartments();
      fetchHODsWithoutDepartment();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (department) => {
    setEditDepartmentId(department.id);
    setEditDepartmentName(department.name);
    setEditHodId(department.hod_id || '');
  };

  const handleUpdateDepartment = async (e, departmentId) => {
    e.preventDefault();
    if (!editDepartmentName.trim()) {
      setError('Department name cannot be empty');
      return;
    }
    try {
      setLoading(true);
      setError('');
      await departmentService.updateDepartment(departmentId, {
        name: editDepartmentName,
        hod_id: editHodId || null,
      });
      setEditDepartmentId(null);
      setEditDepartmentName('');
      setEditHodId('');
      fetchDepartments();
      fetchHODsWithoutDepartment();
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDepartment = async (departmentId) => {
    if (window.confirm('Are you sure you want to delete this department?')) {
      try {
        setLoading(true);
        setError('');
        await departmentService.deleteDepartment(departmentId);
        fetchDepartments();
        fetchHODsWithoutDepartment();
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="card-title">Department Management</h3>
      </div>
      <div className="card-body">
        {error && <div className="alert alert-error">{error}</div>}

        <h4>Create New Department</h4>
        <form onSubmit={handleCreateDepartment}>
          <div className="form-group">
            <label htmlFor="newDepartmentName">Department Name</label>
            <input
              type="text"
              id="newDepartmentName"
              className="form-input"
              value={newDepartmentName}
              onChange={(e) => setNewDepartmentName(e.target.value)}
              placeholder="Enter department name"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="selectedHodId">Assign HOD (Optional)</label>
            <select
              id="selectedHodId"
              className="form-select"
              value={selectedHodId}
              onChange={(e) => setSelectedHodId(e.target.value)}
            >
              <option value="">Select HOD</option>
              {hodsWithoutDepartment.map((hod) => (
                <option key={hod.id} value={hod.id}>
                  {hod.first_name} {hod.last_name}
                </option>
              ))}
            </select>
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Department'}
          </button>
        </form>

        <h4 className="mt-5">Existing Departments</h4>
        {departments.length === 0 && !loading && <p>No departments found.</p>}
        {loading && <p>Loading departments...</p>}
        {!loading && departments.length > 0 && (
          <table className="table table-striped mt-3">
            <thead>
              <tr>
                <th>Name</th>
                <th>HOD</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {departments.map((department) => (
                <tr key={department.id}>
                  <td>
                    {editDepartmentId === department.id ? (
                      <input
                        type="text"
                        className="form-input"
                        value={editDepartmentName}
                        onChange={(e) => setEditDepartmentName(e.target.value)}
                      />
                    ) : (
                      department.name
                    )}
                  </td>
                  <td>
                    {editDepartmentId === department.id ? (
                      <select
                        className="form-select"
                        value={editHodId}
                        onChange={(e) => setEditHodId(e.target.value)}
                      >
                        <option value="">Select HOD</option>
                        {hodsWithoutDepartment.map((hod) => (
                          <option key={hod.id} value={hod.id}>
                            {hod.first_name} {hod.last_name}
                          </option>
                        ))}
                        {department.hod_id && !hodsWithoutDepartment.some(hod => hod.id === department.hod_id) && (
                            <option key={department.hod_id} value={department.hod_id}>
                                {department.hod_name} (Current)
                            </option>
                        )}
                      </select>
                    ) : (
                      department.hod_name || 'N/A'
                    )}
                  </td>
                  <td>
                    {editDepartmentId === department.id ? (
                      <div className="btn-group">
                        <button
                          className="btn btn-success btn-sm"
                          onClick={(e) => handleUpdateDepartment(e, department.id)}
                          disabled={loading}
                        >
                          Save
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setEditDepartmentId(null)}
                          disabled={loading}
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="btn-group">
                        <button
                          className="btn btn-info btn-sm"
                          onClick={() => handleEditClick(department)}
                          disabled={loading}
                        >
                          Edit
                        </button>
                        <button
                          className="btn btn-danger btn-sm"
                          onClick={() => handleDeleteDepartment(department.id)}
                          disabled={loading}
                        >
                          Delete
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default DepartmentManagement;

