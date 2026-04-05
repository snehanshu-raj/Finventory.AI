import axios from 'axios';
import toast from 'react-hot-toast';
import { useUserStore } from '@/store/userStore';

// Determine API base URL based on environment
const getBaseURL = () => {
  // If running on localhost, connect directly to backend
  if (typeof window !== 'undefined' && window.location.hostname === 'localhost') {
    return 'http://localhost:8000';
  }
  // Otherwise use relative paths (works for ngrok, production, etc.)
  return '/';
};

const client = axios.create({
  baseURL: getBaseURL(),
  timeout: 30_000,
});

// Request interceptor: attach userId as query param
client.interceptors.request.use((config) => {
  const { userId } = useUserStore.getState();
  if (userId) {
    config.params = { ...config.params, user_id: userId };
  }
  return config;
});

// Response interceptor: unwrap success envelope, handle errors
client.interceptors.response.use(
  (res) => res.data?.data ?? res.data,
  (err) => {
    const msg = err.response?.data?.error?.message || err.message || 'Something went wrong';
    toast.error(msg);
    return Promise.reject(err);
  }
);

export default client;
