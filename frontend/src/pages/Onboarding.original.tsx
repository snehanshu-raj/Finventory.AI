import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { ChevronRight, ChevronLeft, Check, User, Home, ShoppingBasket, Settings, ClipboardCheck } from 'lucide-react';
import toast from 'react-hot-toast';
import { usersApi } from '@/api/users';
import { useUserStore } from '@/store/userStore';
import { DEFAULT_STAPLES, CURRENCIES, UNIT_OPTIONS } from '@/utils/constants';

const steps = [
  { icon: User, label: 'Personal Info' },
  { icon: Home, label: 'Household' },
  { icon: ShoppingBasket, label: 'Staples' },
  { icon: Settings, label: 'Preferences' },
  { icon: ClipboardCheck, label: 'Review' },
];

const personalSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email required'),
});

interface StapleItem {
  enabled: boolean;
  canonical_name: string;
  daily_consumption_estimate: number;
  unit: string;
  threshold_quantity: number;
}

export default function Onboarding() {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();
  const setUser = useUserStore((s) => s.setUser);

  // Step 1 form
  const { register: regPersonal, handleSubmit: handlePersonal, formState: { errors: errPersonal }, getValues: getPersonalValues } =
    useForm({ resolver: zodResolver(personalSchema), defaultValues: { name: '', email: '' } });

  // Step 2 state
  const [household, setHousehold] = useState({ household_size: 2, adults: 2, children: 0 });

  // Step 3 state
  const [staples, setStaples] = useState<StapleItem[]>(
    DEFAULT_STAPLES.map((s) => ({
      enabled: true,
      canonical_name: s.name,
      daily_consumption_estimate: s.daily,
      unit: s.unit,
      threshold_quantity: s.threshold,
    }))
  );

  // Step 4 state
  const [prefs, setPrefs] = useState({
    currency: 'USD',
    notification_enabled: true,
    notification_channels: ['in_app'] as string[],
  });

  const mutation = useMutation({
    mutationFn: usersApi.onboard,
    onSuccess: (data) => {
      const d = data as unknown as { id: string; name: string; email: string };
      setUser(d.id, d.name, d.email);
      toast.success('Welcome to Finventory! 🎉');
      navigate('/');
    },
    onError: () => {
      toast.error('Onboarding failed. Please try again.');
    },
  });

  const next = () => {
    if (step === 0) {
      handlePersonal(() => setStep(1))();
    } else if (step < 4) {
      setStep(step + 1);
    }
  };
  const back = () => step > 0 && setStep(step - 1);

  const submit = () => {
    const personal = getPersonalValues();
    const enabledStaples = staples.filter((s) => s.enabled);
    mutation.mutate({
      name: personal.name,
      email: personal.email,
      household_profile: household,
      diet_profile: {
        staples: enabledStaples.map((s) => ({
          canonical_item_id: s.canonical_name.toLowerCase().replace(/\s+/g, '_'),
          canonical_name: s.canonical_name,
          daily_consumption_estimate: s.daily_consumption_estimate,
          unit: s.unit,
          threshold_quantity: s.threshold_quantity,
        })),
      },
      preferences: {
        currency: prefs.currency,
        locale: 'en-US',
        notification_enabled: prefs.notification_enabled,
        notification_channels: prefs.notification_channels,
      },
    });
  };

  const toggleStaple = (i: number) =>
    setStaples((prev) => prev.map((s, idx) => (idx === i ? { ...s, enabled: !s.enabled } : s)));

  const updateStaple = (i: number, field: keyof StapleItem, value: string | number) =>
    setStaples((prev) => prev.map((s, idx) => (idx === i ? { ...s, [field]: value } : s)));

  const addCustomStaple = () =>
    setStaples((prev) => [
      ...prev,
      { enabled: true, canonical_name: '', daily_consumption_estimate: 0.1, unit: 'count', threshold_quantity: 1 },
    ]);

  return (
    <div className="min-h-screen bg-bg flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-2">
            <span className="bg-gradient-to-r from-sky-400 to-cyan-300 bg-clip-text text-transparent">🧠 Finventory.AI</span>
          </h1>
          <p className="text-muted">Set up your smart pantry in a few easy steps</p>
        </div>

        {/* Progress */}
        <div className="flex items-center justify-between mb-8 px-4">
          {steps.map((s, i) => (
            <div key={s.label} className="flex items-center">
              <div className={`flex items-center gap-1.5 ${i <= step ? 'text-sky-400' : 'text-muted'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all
                  ${i < step ? 'bg-sky-500 text-white' : i === step ? 'bg-sky-500/20 text-sky-400 ring-2 ring-sky-400' : 'bg-surface-2'}`}>
                  {i < step ? <Check size={16} /> : i + 1}
                </div>
                <span className="hidden md:block text-xs font-medium">{s.label}</span>
              </div>
              {i < steps.length - 1 && (
                <div className={`w-8 md:w-16 h-0.5 mx-1 ${i < step ? 'bg-sky-400' : 'bg-surface-2'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Card */}
        <div className="bg-surface rounded-2xl border border-border p-6 md:p-8 shadow-xl">
          <AnimatePresence mode="wait">
            <motion.div
              key={step}
              initial={{ opacity: 0, x: 40 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -40 }}
              transition={{ duration: 0.25 }}
            >
              {/* Step 1: Personal */}
              {step === 0 && (
                <div className="space-y-5">
                  <h2 className="text-xl font-semibold">Personal Information</h2>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Name</label>
                    <input {...regPersonal('name')} placeholder="Your name"
                      className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none" />
                    {errPersonal.name && <p className="text-red-400 text-xs mt-1">{errPersonal.name.message}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Email</label>
                    <input {...regPersonal('email')} type="email" placeholder="you@example.com"
                      className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm focus:ring-2 focus:ring-sky-500 focus:border-transparent outline-none" />
                    {errPersonal.email && <p className="text-red-400 text-xs mt-1">{errPersonal.email.message}</p>}
                  </div>
                </div>
              )}

              {/* Step 2: Household */}
              {step === 1 && (
                <div className="space-y-5">
                  <h2 className="text-xl font-semibold">Household Profile</h2>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Household Size</label>
                    <div className="flex items-center gap-3">
                      <button onClick={() => setHousehold((h) => ({ ...h, household_size: Math.max(1, h.household_size - 1), adults: Math.min(h.adults, Math.max(1, h.household_size - 1)) }))}
                        className="w-10 h-10 rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-lg font-bold hover:bg-[var(--color-surface-2)] transition-colors">−</button>
                      <span className="text-2xl font-bold w-10 text-center">{household.household_size}</span>
                      <button onClick={() => setHousehold((h) => ({ ...h, household_size: Math.min(10, h.household_size + 1) }))}
                        className="w-10 h-10 rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-lg font-bold hover:bg-[var(--color-surface-2)] transition-colors">+</button>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Adults</label>
                    <div className="flex items-center gap-3">
                      <button onClick={() => setHousehold((h) => ({ ...h, adults: Math.max(1, h.adults - 1), children: h.household_size - Math.max(1, h.adults - 1) }))}
                        className="w-10 h-10 rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-lg font-bold hover:bg-[var(--color-surface-2)] transition-colors">−</button>
                      <span className="text-2xl font-bold w-10 text-center">{household.adults}</span>
                      <button onClick={() => setHousehold((h) => ({ ...h, adults: Math.min(h.household_size, h.adults + 1), children: h.household_size - Math.min(h.household_size, h.adults + 1) }))}
                        className="w-10 h-10 rounded-lg bg-[var(--color-bg)] border border-[var(--color-border)] flex items-center justify-center text-lg font-bold hover:bg-[var(--color-surface-2)] transition-colors">+</button>
                    </div>
                  </div>
                  <div className="bg-[var(--color-bg)] rounded-lg p-3 border border-[var(--color-border)]">
                    <p className="text-sm text-[var(--color-muted)]">Children (auto): <span className="font-semibold text-[var(--color-text)]">{household.household_size - household.adults}</span></p>
                  </div>
                </div>
              )}

              {/* Step 3: Staples */}
              {step === 2 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold">Staple Items</h2>
                    <button onClick={addCustomStaple}
                      className="text-sm text-sky-400 hover:text-sky-300 font-medium">+ Add Custom</button>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
                    {staples.map((s, i) => (
                      <div key={i} className={`rounded-xl border p-3 transition-all ${s.enabled ? 'border-sky-500/40 bg-sky-500/5' : 'border-[var(--color-border)] opacity-50'}`}>
                        <div className="flex items-center gap-2 mb-2">
                          <button onClick={() => toggleStaple(i)}
                            className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${s.enabled ? 'bg-sky-500 border-sky-500' : 'border-[var(--color-muted)]'}`}>
                            {s.enabled && <Check size={12} className="text-white" />}
                          </button>
                          <input value={s.canonical_name} onChange={(e) => updateStaple(i, 'canonical_name', e.target.value)}
                            className="flex-1 bg-transparent text-sm font-medium outline-none capitalize"
                            placeholder="Item name" />
                        </div>
                        {s.enabled && (
                          <div className="grid grid-cols-3 gap-2 text-xs">
                            <div>
                              <label className="text-[var(--color-muted)]">Daily</label>
                              <input type="number" step="0.01" value={s.daily_consumption_estimate}
                                onChange={(e) => updateStaple(i, 'daily_consumption_estimate', parseFloat(e.target.value) || 0)}
                                className="w-full mt-0.5 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm outline-none focus:ring-1 focus:ring-sky-500" />
                            </div>
                            <div>
                              <label className="text-[var(--color-muted)]">Unit</label>
                              <select value={s.unit} onChange={(e) => updateStaple(i, 'unit', e.target.value)}
                                className="w-full mt-0.5 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm outline-none focus:ring-1 focus:ring-sky-500">
                                {UNIT_OPTIONS.map((u) => <option key={u} value={u}>{u}</option>)}
                              </select>
                            </div>
                            <div>
                              <label className="text-[var(--color-muted)]">Threshold</label>
                              <input type="number" step="0.1" value={s.threshold_quantity}
                                onChange={(e) => updateStaple(i, 'threshold_quantity', parseFloat(e.target.value) || 0)}
                                className="w-full mt-0.5 px-2 py-1 bg-[var(--color-bg)] border border-[var(--color-border)] rounded text-sm outline-none focus:ring-1 focus:ring-sky-500" />
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Step 4: Preferences */}
              {step === 3 && (
                <div className="space-y-5">
                  <h2 className="text-xl font-semibold">Preferences</h2>
                  <div>
                    <label className="block text-sm font-medium mb-1.5">Currency</label>
                    <select value={prefs.currency} onChange={(e) => setPrefs((p) => ({ ...p, currency: e.target.value }))}
                      className="w-full px-4 py-2.5 bg-[var(--color-bg)] border border-[var(--color-border)] rounded-lg text-sm outline-none focus:ring-2 focus:ring-sky-500">
                      {CURRENCIES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
                    </select>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Enable Notifications</span>
                    <button onClick={() => setPrefs((p) => ({ ...p, notification_enabled: !p.notification_enabled }))}
                      className={`w-11 h-6 rounded-full p-0.5 transition-colors ${prefs.notification_enabled ? 'bg-sky-500' : 'bg-[var(--color-surface-2)]'}`}>
                      <div className={`w-5 h-5 rounded-full bg-white transition-transform ${prefs.notification_enabled ? 'translate-x-5' : ''}`} />
                    </button>
                  </div>
                </div>
              )}

              {/* Step 5: Review */}
              {step === 4 && (
                <div className="space-y-4">
                  <h2 className="text-xl font-semibold">Review & Submit</h2>
                  <div className="space-y-3">
                    <div className="bg-[var(--color-bg)] rounded-lg p-4 border border-[var(--color-border)]">
                      <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase mb-2">Personal</h3>
                      <p className="text-sm">{getPersonalValues().name} — {getPersonalValues().email}</p>
                    </div>
                    <div className="bg-[var(--color-bg)] rounded-lg p-4 border border-[var(--color-border)]">
                      <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase mb-2">Household</h3>
                      <p className="text-sm">{household.household_size} people ({household.adults} adults, {household.household_size - household.adults} children)</p>
                    </div>
                    <div className="bg-[var(--color-bg)] rounded-lg p-4 border border-[var(--color-border)]">
                      <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase mb-2">Staples ({staples.filter((s) => s.enabled).length})</h3>
                      <div className="flex flex-wrap gap-1.5">{staples.filter((s) => s.enabled).map((s, i) =>
                        <span key={i} className="px-2 py-0.5 bg-sky-500/10 text-sky-400 rounded text-xs font-medium capitalize">{s.canonical_name}</span>)}
                      </div>
                    </div>
                    <div className="bg-[var(--color-bg)] rounded-lg p-4 border border-[var(--color-border)]">
                      <h3 className="text-xs font-semibold text-[var(--color-muted)] uppercase mb-2">Preferences</h3>
                      <p className="text-sm">{prefs.currency} • Notifications {prefs.notification_enabled ? 'On' : 'Off'}</p>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-5 border-t border-[var(--color-border)]">
            <button onClick={back} disabled={step === 0}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all
                ${step === 0 ? 'opacity-0 pointer-events-none' : 'hover:bg-[var(--color-surface-2)]'}`}>
              <ChevronLeft size={16} /> Back
            </button>
            {step < 4 ? (
              <button onClick={next}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-sky-500/25">
                Next <ChevronRight size={16} />
              </button>
            ) : (
              <button onClick={submit} disabled={mutation.isPending}
                className="flex items-center gap-1.5 px-5 py-2.5 bg-gradient-to-r from-sky-500 to-cyan-400 hover:from-sky-600 hover:to-cyan-500 text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-sky-500/25 disabled:opacity-50">
                {mutation.isPending ? 'Setting up...' : 'Complete Setup'} <Check size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
