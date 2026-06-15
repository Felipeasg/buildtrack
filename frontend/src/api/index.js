import axios from "axios";

// Auth is disabled for local testing: no token is attached and the backend
// runs every request as a fixed demo user.
const api = axios.create({ baseURL: "/api" });

// Milestones
export const listMilestones = () => api.get("/milestones");
export const getMilestone = (id) => api.get(`/milestones/${id}`);
export const createMilestone = (data) => api.post("/milestones", data);
export const updateMilestone = (id, data) => api.patch(`/milestones/${id}`, data);
export const deleteMilestone = (id) => api.delete(`/milestones/${id}`);
export const getBurndown = (id) => api.get(`/milestones/${id}/burndown`);

// Tasks
export const createTask = (milestoneId, data) =>
  api.post(`/milestones/${milestoneId}/tasks`, data);
export const updateTask = (taskId, data) => api.patch(`/tasks/${taskId}`, data);
export const deleteTask = (taskId) => api.delete(`/tasks/${taskId}`);

// Tags
export const listTags = () => api.get("/tags");
export const createTag = (data) => api.post("/tags", data);

export default api;
