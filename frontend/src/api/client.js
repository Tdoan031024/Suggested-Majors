import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
});

export const fetchGroups = () => API.get('/api/groups');
export const fetchTohop = () => API.get('/api/tohop');
export const fetchTohopByGroup = (group) =>
  API.get(`/api/tohop/by-group/${encodeURIComponent(group)}`);

export const predictDGNL = (data) => API.post('/api/dgnl', data);
export const predictHocBa = (data) => API.post('/api/hocba', data);
export const predictTuyenThang = (data) => API.post('/api/tuyenthang', data);
export const predictTHPT = (data) => API.post('/api/thpt', data);

export default API;
