import axios from "axios";

const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

// Auth
export const login = (email, password) => {
  const form = new URLSearchParams();
  form.append("username", email);
  form.append("password", password);
  return api.post("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
};
export const register = (data) => api.post("/auth/register", data);
export const getMe = () => api.get("/auth/me");

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

// Import
export const importCsv = (file) => {
  const form = new FormData();
  form.append("file", file);
  return api.post("/import/csv", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export default api;
