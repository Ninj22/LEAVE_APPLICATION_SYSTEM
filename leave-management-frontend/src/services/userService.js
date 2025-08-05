// src/services/userService.js

import axios from 'axios';

const API_URL = 'http://localhost:5000/api'; // change if your backend uses a different port

export const getAllUsers = async () => {
  return await axios.get(`${API_URL}/users`);
};

export const getUserById = async (id) => {
  return await axios.get(`${API_URL}/users/${id}`);
};

export const createUser = async (userData) => {
  return await axios.post(`${API_URL}/users`, userData);
};

export const updateUser = async (id, userData) => {
  return await axios.put(`${API_URL}/users/${id}`, userData);
};

export const deleteUser = async (id) => {
  return await axios.delete(`${API_URL}/users/${id}`);
};
