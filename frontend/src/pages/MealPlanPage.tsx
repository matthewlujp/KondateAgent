import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { MealSlotCard, ChatPanel } from '../components';
import { mealPlansApi } from '../api';
import type { MealPlan, ChatMessage, DayOfWeek, ALL_DAYS, ScoredRecipe } from '../types';

const ALL_DAYS_LIST: DayOfWeek[] = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
  'sunday',
];

/**
 * MealPlanPage Component
 *
 * Main page for meal plan generation and refinement.
 *
 * Flow:
 * 1. Load recipes from sessionStorage (set by IngredientCollectionPage)
 * 2. Show day toggle grid (weekdays enabled by default)
 * 3. Generate meal plan from selected recipes and enabled days
 * 4. Display week grid with MealSlotCard for each day
 * 5. Allow chat-based refinement via ChatPanel
 *
 * Features:
 * - Day toggle selection before generation
 * - LLM-powered recipe-to-day assignment
 * - Chat interface for swapping meals
 * - Real-time plan updates after swaps
 */
export function MealPlanPage() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get('session_id');

  // State
  const [recipes, setRecipes] = useState<ScoredRecipe[]>([]);
  const [enabledDays, setEnabledDays] = useState<Set<DayOfWeek>>(
    new Set(['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
  );
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load recipes from sessionStorage on mount
  useEffect(() => {
    const storedRecipes = sessionStorage.getItem('mealplan_recipes');
    if (storedRecipes) {
      try {
        const parsed = JSON.parse(storedRecipes);
        setRecipes(parsed);
      } catch (err) {
        console.error('Failed to parse stored recipes:', err);
        setError('Failed to load recipes. Please go back and search again.');
      }
    } else {
      setError('No recipes found. Please go back and complete ingredient collection.');
    }
  }, []);

  const toggleDay = (day: DayOfWeek) => {
    setEnabledDays((prev) => {
      const next = new Set(prev);
      if (next.has(day)) {
        next.delete(day);
      } else {
        next.add(day);
      }
      return next;
    });
  };

  const handleGeneratePlan = async () => {
    if (!sessionId) {
      setError('No session ID found');
      return;
    }

    if (enabledDays.size === 0) {
      setError('Please select at least one day');
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      const recipeIds = recipes.map((sr) => sr.recipe.id);
      const generatedPlan = await mealPlansApi.generatePlan({
        ingredient_session_id: sessionId,
        enabled_days: Array.from(enabledDays),
        recipe_ids: recipeIds,
      });

      setPlan(generatedPlan);
      setChatMessages([]);
    } catch (err) {
      console.error('Failed to generate plan:', err);
      setError('Failed to generate meal plan. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSendChatMessage = async (message: string) => {
    if (!plan) return;

    setIsChatLoading(true);
    setError(null);

    // Add user message optimistically
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    try {
      const response = await mealPlansApi.sendChatMessage(plan.id, message);

      // Update plan with potentially modified slots
      setPlan(response.plan);

      // Add assistant message
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        tool_calls: response.tool_calls.length > 0 ? response.tool_calls : undefined,
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to send chat message:', err);
      setError('Failed to process your request. Please try again.');
      // Remove optimistic user message on error
      setChatMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsChatLoading(false);
    }
  };

  // Build recipe lookup map
  const recipeMap = new Map(recipes.map((sr) => [sr.recipe.id, sr.recipe]));

  return (
    <div className="min-h-screen bg-cream">
      {/* Header */}
      <header className="bg-gradient-to-r from-terra-500 to-herb-500 text-white py-8 shadow-lg">
        <div className="max-w-5xl mx-auto px-4">
          <h1 className="text-3xl font-bold mb-2">Your Weekly Meal Plan</h1>
          <p className="text-terra-100">
            {plan
              ? 'Review your plan and make changes via chat'
              : 'Select days to plan meals for'}
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-chili-50 border border-chili-200 rounded-lg">
            <p className="text-sm text-chili-700">{error}</p>
          </div>
        )}

        {!plan ? (
          /* Pre-generation: Day Toggle Grid */
          <div className="bg-white border border-sand-200 rounded-xl shadow-warm p-6">
            <h2 className="text-xl font-semibold text-sand-900 mb-4">
              Which days would you like to plan?
            </h2>
            <p className="text-sm text-sand-600 mb-6">
              Select the days you'd like meal suggestions for. Weekdays are selected by default.
            </p>

            {/* Day Toggle Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
              {ALL_DAYS_LIST.map((day) => {
                const isEnabled = enabledDays.has(day);
                const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);

                return (
                  <button
                    key={day}
                    onClick={() => toggleDay(day)}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      isEnabled
                        ? 'border-terra-500 bg-terra-50 text-terra-700'
                        : 'border-sand-200 bg-white text-sand-500 hover:border-sand-300'
                    }`}
                  >
                    <div className="text-sm font-semibold">{dayLabel}</div>
                    {isEnabled && (
                      <svg
                        className="w-5 h-5 mx-auto mt-1 text-terra-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </button>
                );
              })}
            </div>

            {/* Generate Button */}
            <div className="flex justify-center">
              <button
                onClick={handleGeneratePlan}
                disabled={isGenerating || enabledDays.size === 0 || recipes.length === 0}
                className="px-8 py-3 bg-terra-500 text-white rounded-lg font-semibold hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed"
              >
                {isGenerating ? (
                  <span className="flex items-center">
                    <svg
                      className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                    Generating...
                  </span>
                ) : (
                  'Plan My Meals!'
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Post-generation: Week Grid + Chat */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Week Grid */}
            <div className="lg:col-span-2">
              <h2 className="text-xl font-semibold text-sand-900 mb-4">
                Your Week at a Glance
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {plan.slots
                  .sort((a, b) => {
                    const dayOrder = {
                      monday: 0,
                      tuesday: 1,
                      wednesday: 2,
                      thursday: 3,
                      friday: 4,
                      saturday: 5,
                      sunday: 6,
                    };
                    return dayOrder[a.day] - dayOrder[b.day];
                  })
                  .map((slot) => (
                    <MealSlotCard
                      key={slot.id}
                      slot={slot}
                      recipe={slot.recipe_id ? recipeMap.get(slot.recipe_id) : undefined}
                    />
                  ))}
              </div>
            </div>

            {/* Chat Panel */}
            <div className="lg:col-span-1">
              <div className="sticky top-4 h-[600px]">
                <ChatPanel
                  messages={chatMessages}
                  onSendMessage={handleSendChatMessage}
                  isLoading={isChatLoading}
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
