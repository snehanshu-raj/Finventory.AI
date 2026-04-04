import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { usersApi } from '@/api/users';
import { useUserStore } from '@/store/userStore';

export default function Onboarding() {
  const navigate = useNavigate();
  const setUser = useUserStore((s) => s.setUser);
  
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');

  const mutation = useMutation({
    mutationFn: (data: any) => usersApi.onboard(data),
    onSuccess: (data: any) => {
      console.log('✅ Onboarding success:', data);
      setUser(data.id, data.name, data.email);
      toast.success('All set! Welcome!');
      navigate('/');
    },
    onError: (error: any) => {
      console.error('❌ Onboarding error:', error);
      toast.error('Onboarding failed');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    toast.loading('Setting up your account...');

    const payload = {
      name,
      email,
      household_profile: {
        household_size: 2,
        adults: 2,
        children: 0,
      },
      diet_profile: {
        staples: [
          {
            canonical_item_id: 'rice',
            canonical_name: 'Rice',
            daily_consumption_estimate: 0.2,
            unit: 'kg',
            threshold_quantity: 2,
          },
        ],
      },
      preferences: {
        currency: 'USD',
        locale: 'en-US',
        notification_enabled: true,
        notification_channels: ['in_app'],
      },
    };

    mutation.mutate(payload);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0f172a] via-[#1a2744] to-[#0f172a] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="bg-surface rounded-2xl border border-border p-8 shadow-2xl">
          <h1 className="text-4xl font-bold text-text mb-2">Finventory</h1>
          <p className="text-muted mb-8">Let's get started</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text mb-2">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your name"
                required
                className="w-full px-4 py-2.5 bg-bg border border-border rounded-lg text-text placeholder-muted focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none transition-all"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full px-4 py-2.5 bg-bg border border-border rounded-lg text-text placeholder-muted focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={mutation.isPending}
              className="w-full bg-gradient-to-r from-sky-500 to-cyan-500 hover:from-sky-600 hover:to-cyan-600 disabled:opacity-50 text-white font-semibold py-2.5 rounded-lg transition-all shadow-lg shadow-sky-500/25 mt-6"
            >
              {mutation.isPending ? 'Setting up...' : 'Complete Setup'}
            </button>
          </form>

          {mutation.isError && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              Something went wrong. Please try again.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
