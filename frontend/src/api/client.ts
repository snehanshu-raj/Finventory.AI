import axios from 'axios';
import toast from 'react-hot-toast';
import { useUserStore } from '@/store/userStore';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
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
