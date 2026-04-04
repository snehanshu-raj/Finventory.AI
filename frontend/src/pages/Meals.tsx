import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { ChefHat, Clock, Check, X, Sparkles } from 'lucide-react';
import { mealsApi, type Meal } from '@/api/meals';
import { useUserStore } from '@/store/userStore';
import { Card } from '@/components/ui/Card';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';

export default function Meals() {
  const userId = useUserStore((s) => s.userId) ?? '';
  const [maxPrep, setMaxPrep] = useState(30);
  const [vegetarian, setVegetarian] = useState(false);
  const [budgetMode, setBudgetMode] = useState(false);

  const mutation = useMutation({
    mutationFn: () => mealsApi.suggest({
      user_id: userId,
      constraints: { max_prep_minutes: maxPrep, vegetarian, budget_mode: budgetMode },
    }),
  });

  const meals = (mutation.data as unknown as { meals: Meal[] })?.meals ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Meal Suggestions</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Constraints */}
        <Card>
          <h2 className="text-sm font-semibold text-[var(--color-muted)] uppercase mb-4">Preferences</h2>
          <div className="space-y-5">
            <div>
              <label className="flex items-center justify-between text-sm font-medium mb-2">
                <span>Max Prep Time</span>
                <span className="text-sky-400 font-mono">{maxPrep} min</span>
              </label>
              <input type="range" min={5} max={120} step={5} value={maxPrep} onChange={(e) => setMaxPrep(+e.target.value)}
                className="w-full accent-sky-500" />
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Vegetarian</span>
              <button onClick={() => setVegetarian(!vegetarian)}
                className={`w-11 h-6 rounded-full p-0.5 transition-colors ${vegetarian ? 'bg-green-500' : 'bg-[var(--color-surface-2)]'}`}>
                <div className={`w-5 h-5 rounded-full bg-white transition-transform ${vegetarian ? 'translate-x-5' : ''}`} />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Budget Mode</span>
              <button onClick={() => setBudgetMode(!budgetMode)}
                className={`w-11 h-6 rounded-full p-0.5 transition-colors ${budgetMode ? 'bg-sky-500' : 'bg-[var(--color-surface-2)]'}`}>
                <div className={`w-5 h-5 rounded-full bg-white transition-transform ${budgetMode ? 'translate-x-5' : ''}`} />
              </button>
            </div>

            <button onClick={() => mutation.mutate()} disabled={mutation.isPending}
              className="w-full py-2.5 bg-gradient-to-r from-sky-500 to-cyan-400 hover:from-sky-600 hover:to-cyan-500 text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-sky-500/20 flex items-center justify-center gap-2 disabled:opacity-50">
              <Sparkles size={16} /> {mutation.isPending ? 'Generating...' : 'Suggest Meals'}
            </button>
          </div>
        </Card>

        {/* Right: Meal Cards */}
        <div className="lg:col-span-2 space-y-4">
          {mutation.isPending && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[...Array(2)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
          )}

          {!mutation.isPending && meals.length === 0 && !mutation.isSuccess && (
            <EmptyState icon={ChefHat} title="Ready to cook?" description="Set your preferences and click 'Suggest Meals' to get personalized recipes based on your pantry." />
          )}

          {!mutation.isPending && mutation.isSuccess && meals.length === 0 && (
            <EmptyState icon={ChefHat} title="Your pantry is empty" description="Upload a receipt to stock your pantry, then come back for meal ideas!" />
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {meals.map((meal, i) => (
              <motion.div key={meal.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
                <Card hover className="h-full">
                  <h3 className="text-lg font-semibold mb-1">{meal.title}</h3>
                  <p className="text-sm text-[var(--color-muted)] mb-3">{meal.description}</p>

                  <div className="flex items-center gap-1.5 mb-3">
                    <Clock size={14} className="text-sky-400" />
                    <span className="text-xs text-sky-400 font-medium">{meal.prep_time_minutes} min</span>
                  </div>

                  <div className="space-y-2 mb-3">
                    <p className="text-xs font-semibold text-[var(--color-muted)] uppercase">From Your Pantry</p>
                    <div className="flex flex-wrap gap-1.5">
                      {meal.pantry_ingredients_used.map((ing) => (
                        <span key={ing} className="inline-flex items-center gap-1 px-2 py-0.5 bg-green-500/10 text-green-400 rounded text-xs font-medium capitalize">
                          <Check size={10} />{ing}
                        </span>
                      ))}
                    </div>
                  </div>

                  {meal.missing_ingredients.length > 0 && (
                    <div className="space-y-2 mb-3">
                      <p className="text-xs font-semibold text-[var(--color-muted)] uppercase">Need to Buy</p>
                      <div className="flex flex-wrap gap-1.5">
                        {meal.missing_ingredients.map((ing) => (
                          <span key={ing} className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-500/10 text-red-400 rounded text-xs font-medium capitalize">
                            <X size={10} />{ing}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <p className="text-xs text-[var(--color-muted)] italic mt-auto">{meal.why_suggested}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
