import api from './authService';

export const leaveService = {
  async getLeaveTypes() {
    try {
      const response = await api.get('/api/leaves/types');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get leave types');
    }
  },

  async getLeaveBalances() {
    try {
      const response = await api.get('/api/leaves/balances');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get leave balances');
    }
  },

  async applyLeave(leaveData) {
    try {
      const response = await api.post('/api/leaves/apply', leaveData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to apply for leave');
    }
  },

  async getUserApplications() {
    try {
      const response = await api.get('/api/leaves/applications');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get applications');
    }
  },

  async getPendingApplications() {
    try {
      const response = await api.get('/api/leaves/pending');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get pending applications');
    }
  },

  async approveRejectApplication(applicationId, action, comments = '') {
    try {
      const response = await api.put(`/api/leaves/approve/${applicationId}`, {
        action,
        comments,
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to process application');
    }
  },

  async getLeaveHistory(filters = {}) {
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.year) params.append('year', filters.year);
      
      const response = await api.get(`/api/leaves/history?${params}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get leave history');
    }
  },

  async getAvailableUsers(startDate, endDate) {
    try {
      const response = await api.get('/api/users/available-for-handover', {
        params: {
          start_date: startDate,
          end_date: endDate,
        },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get available users');
    }
  },
};

export const dashboardService = {
  async getDashboardStats() {
    try {
      const response = await api.get('/api/dashboard/stats');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get dashboard stats');
    }
  },

  async getCalendarData(year, month) {
    try {
      const response = await api.get('/api/dashboard/calendar', {
        params: { year, month },
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get calendar data');
    }
  },

  async getLeaveCountdown() {
    try {
      const response = await api.get('/api/dashboard/countdown');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || 'Failed to get countdown data');
    }
  },
};

export const departmentService = {
  async createDepartment(departmentData) {
    try {
      const response = await api.post("/api/departments/", departmentData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to create department");
    }
  },

  async getDepartments() {
    try {
      const response = await api.get("/api/departments/");
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to get departments");
    }
  },

  async updateDepartment(departmentId, departmentData) {
    try {
      const response = await api.put(`/api/departments/${departmentId}`, departmentData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to update department");
    }
  },

  async deleteDepartment(departmentId) {
    try {
      const response = await api.delete(`/api/departments/${departmentId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to delete department");
    }
  },

  async getHODsWithoutDepartment() {
    try {
      const response = await api.get("/api/departments/hods-without-department");
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to get HODs without department");
    }
  },

  async assignHODToDepartment(departmentId, hodId) {
    try {
      const response = await api.put(`/api/departments/${departmentId}/assign-hod`, { hod_id: hodId });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to assign HOD to department");
    }
  },

  async unassignHODFromDepartment(departmentId) {
    try {
      const response = await api.put(`/api/departments/${departmentId}/unassign-hod`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to unassign HOD from department");
    }
  },

  async assignStaffToDepartment(departmentId, staffIds) {
    try {
      const response = await api.put(`/api/departments/${departmentId}/assign-staff`, { staff_ids: staffIds });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to assign staff to department");
    }
  },

  async unassignStaffFromDepartment(departmentId, staffIds) {
    try {
      const response = await api.put(`/api/departments/${departmentId}/unassign-staff`, { staff_ids: staffIds });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to unassign staff from department");
    }
  },

  async getStaffByDepartment(departmentId) {
    try {
      const response = await api.get(`/api/departments/staff-by-department/${departmentId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.error || "Failed to get staff by department");
    }
  },
};



