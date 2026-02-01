import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  SessionStartModal,
  VoiceInputController,
  TextInputFallback,
  IngredientList,
  RecipeSearchProgress,
  ChannelBanner,
  CollapsibleSection,
  ExpandableMealCard,
  ChatFAB,
  ChatBottomSheet,
  ChatPanel,
} from '../components';
import {
  authApi,
  ingredientsApi,
  streamRecipeSearch,
  tokenManager,
  creatorsApi,
  mealPlansApi,
} from '../api';
import type {
  Ingredient,
  IngredientSession,
  ProgressEvent,
  ScoredRecipe,
  DayOfWeek,
  MealPlan,
  ChatMessage,
} from '../types';
import { ALL_DAYS } from '../types';

const USER_ID = 'demo-user';

const WEEKDAY_DEFAULTS: DayOfWeek[] = [
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
];

/**
 * MealPlanningPage Component
 *
 * Unified page for the entire meal planning workflow:
 * 1. Ingredient collection
 * 2. Recipe search
 * 3. Meal plan generation and refinement
 *
 * Each section is collapsible and has independent refresh buttons.
 */
export function MealPlanningPage() {
  // Session state
  const [session, setSession] = useState<IngredientSession | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [existingSession, setExistingSession] = useState<IngredientSession | null>(
    null
  );

  // UI state
  const [isTextInputExpanded, setIsTextInputExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthReady, setIsAuthReady] = useState(false);

  // Recipe search state
  const [isSearching, setIsSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState<ProgressEvent | null>(null);
  const [searchComplete, setSearchComplete] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [recipes, setRecipes] = useState<ScoredRecipe[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Meal plan state
  const [enabledDays, setEnabledDays] = useState<Set<DayOfWeek>>(
    new Set(WEEKDAY_DEFAULTS)
  );
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Channel banner state
  const [bannerDismissed, setBannerDismissed] = useState(() =>
    localStorage.getItem('channelBannerDismissed') === 'true'
  );

  const { data: creators = [] } = useQuery({
    queryKey: ['creators'],
    queryFn: creatorsApi.getCreators,
    enabled: !bannerDismissed && isAuthReady,
  });

  const showBanner = !bannerDismissed && creators.length === 0;

  const handleDismissBanner = () => {
    localStorage.setItem('channelBannerDismissed', 'true');
    setBannerDismissed(true);
  };

  // Initialize auth token and check for existing session on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  // Cleanup: abort streaming on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const initializeAuth = async (retryCount = 0) => {
    try {
      await ensureValidToken();
      setIsAuthReady(true);
      await checkExistingSession();
    } catch (err: any) {
      console.error('Failed to initialize auth:', err);

      if (err.response?.status === 401 && retryCount === 0) {
        console.log('Token invalid, getting fresh token and retrying...');
        tokenManager.clearToken();
        setIsAuthReady(false);
        return initializeAuth(1);
      }

      setError('Failed to authenticate. Please refresh and try again.');
      setIsAuthReady(false);
    }
  };

  const ensureValidToken = async () => {
    const existingToken = tokenManager.getToken();
    if (!existingToken) {
      const tokenResponse = await authApi.getToken(USER_ID);
      tokenManager.setToken(tokenResponse.access_token);
    }
  };

  const checkExistingSession = async () => {
    try {
      const latest = await ingredientsApi.getLatestSession(USER_ID);
      if (latest && latest.status === 'in_progress') {
        setExistingSession(latest);
        setShowModal(true);
      } else {
        await createNewSession();
      }
    } catch (err: any) {
      console.error('Failed to check existing session:', err);

      if (err.response?.status === 401) {
        throw err;
      }

      await createNewSession();
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await ingredientsApi.createSession(USER_ID);
      setSession(newSession);
    } catch (err: any) {
      console.error('Failed to create session:', err);

      if (err.response?.status === 401) {
        throw err;
      }

      setError('Failed to start session. Please refresh and try again.');
    }
  };

  const handleUpdateExisting = () => {
    setSession(existingSession);
    setShowModal(false);
    setExistingSession(null);
  };

  const handleStartFresh = async () => {
    setShowModal(false);
    setExistingSession(null);
    await createNewSession();
  };

  const handleTextInput = async (text: string) => {
    if (!session) {
      setError('No active session. Please refresh the page.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      const parseResult = await ingredientsApi.parse(text);
      const updatedSession = await ingredientsApi.addIngredients(
        session.id,
        parseResult.ingredients
      );

      setSession(updatedSession);
    } catch (err) {
      console.error('Failed to parse and add ingredients:', err);
      setError('Failed to process ingredients. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceTranscript = async (transcript: string) => {
    await handleTextInput(transcript);
  };

  const handleWakeWord = () => {
    console.log('Wake word detected');
  };

  const handleUpdateIngredient = async (
    id: string,
    updates: Partial<Ingredient>
  ) => {
    if (!session) return;

    const updatedIngredients = session.ingredients.map((ing) =>
      ing.id === id ? { ...ing, ...updates } : ing
    );
    setSession({ ...session, ingredients: updatedIngredients });
  };

  const handleDeleteIngredient = async (id: string) => {
    if (!session) return;

    setIsProcessing(true);
    setError(null);

    try {
      const updatedSession = await ingredientsApi.removeIngredient(session.id, id);
      setSession(updatedSession);
    } catch (err) {
      console.error('Failed to delete ingredient:', err);
      setError('Failed to delete ingredient. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSearchRecipes = async () => {
    if (!session || session.ingredients.length === 0) {
      setError('Please add ingredients first');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      await ingredientsApi.updateStatus(session.id, 'confirmed');
      setIsProcessing(false);

      setSearchProgress(null);
      setSearchComplete(false);
      setSearchError(null);
      setRecipes([]);
      setIsSearching(true);

      const ingredientNames = session.ingredients.map((ing) => ing.name);

      const controller = await streamRecipeSearch({
        ingredients: ingredientNames,
        maxResults: 15,
        onProgress: (progress) => {
          setSearchProgress(progress);
        },
        onResult: (foundRecipes) => {
          setRecipes(foundRecipes);
          setSearchComplete(true);
          setIsSearching(false);
          console.log('Recipe search complete:', foundRecipes);
        },
        onError: (errorMessage) => {
          setSearchError(errorMessage);
          setIsSearching(false);
        },
      });

      abortControllerRef.current = controller;
    } catch (err) {
      console.error('Failed to search recipes:', err);
      setError('Failed to search recipes. Please try again.');
      setIsProcessing(false);
      setIsSearching(false);
    }
  };

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
    if (!session) {
      setError('No session found');
      return;
    }

    if (recipes.length === 0) {
      setError('No recipes found. Please search for recipes first.');
      return;
    }

    if (enabledDays.size === 0) {
      setError('Please select at least one day');
      return;
    }

    setIsGeneratingPlan(true);
    setError(null);

    try {
      const recipeIds = recipes.map((sr) => sr.recipe.id);
      const generatedPlan = await mealPlansApi.generatePlan({
        ingredient_session_id: session.id,
        enabled_days: Array.from(enabledDays),
        recipe_ids: recipeIds,
      });

      setPlan(generatedPlan);
      setChatMessages([]);
    } catch (err) {
      console.error('Failed to generate plan:', err);
      setError('Failed to generate meal plan. Please try again.');
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleSendChatMessage = async (message: string) => {
    if (!plan) return;

    setIsChatLoading(true);
    setError(null);

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setChatMessages((prev) => [...prev, userMessage]);

    try {
      const response = await mealPlansApi.sendChatMessage(plan.id, message);

      setPlan(response.plan);

      if (response.recipes && response.recipes.length > 0) {
        setRecipes((prev) => {
          const existingIds = new Set(prev.map((sr) => sr.recipe.id));
          const newRecipes = response.recipes.filter(
            (r) => !existingIds.has(r.id)
          );
          const newScoredRecipes = newRecipes.map((recipe) => ({
            recipe,
            coverage_score: 1.0,
            missing_ingredients: [],
            reasoning: 'Selected via chat refinement',
          }));
          return [...prev, ...newScoredRecipes];
        });
      }

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        tool_calls:
          response.tool_calls.length > 0 ? response.tool_calls : undefined,
        timestamp: new Date().toISOString(),
      };
      setChatMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.error('Failed to send chat message:', err);
      setError('Failed to process your request. Please try again.');
      setChatMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsChatLoading(false);
    }
  };

  // Build recipe lookup map
  const recipeMap = new Map(recipes.map((sr) => [sr.recipe.id, sr.recipe]));

  return (
    <div className="min-h-screen bg-cream bg-kitchen-pattern pb-32">
      {/* Header */}
      <header className="bg-header-gradient shadow-warm-md sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white font-display">
              Plan Your Meals
            </h1>
            <p className="text-sm text-terra-50 mt-1">
              From ingredients to weekly plan
            </p>
          </div>
          <Link
            to="/settings"
            className="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            aria-label="Settings"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </Link>
        </div>
      </header>

      {/* Session Start Modal */}
      <SessionStartModal
        isOpen={showModal}
        ingredientCount={existingSession?.ingredients.length || 0}
        lastUpdated={existingSession?.updated_at || ''}
        onUpdateExisting={handleUpdateExisting}
        onStartFresh={handleStartFresh}
      />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Error Display */}
        {error && (
          <div className="bg-chili-50 border-2 border-chili-300 rounded-lg p-4">
            <p className="text-sm text-chili-800">{error}</p>
          </div>
        )}

        {/* Channel Banner */}
        {showBanner && <ChannelBanner onDismiss={handleDismissBanner} />}

        {/* Section 1: Ingredients */}
        <CollapsibleSection title="§ Ingredients" defaultExpanded={true}>
          <div className="space-y-6">
            {/* Voice Input */}
            <div>
              <h3 className="text-sm font-semibold text-sand-900 mb-3 text-center">
                Add Ingredients
              </h3>
              <VoiceInputController
                onTranscript={handleVoiceTranscript}
                onWakeWord={handleWakeWord}
              />
            </div>

            {/* Text Input Fallback */}
            <TextInputFallback
              onSubmit={handleTextInput}
              isExpanded={isTextInputExpanded}
              onToggle={() => setIsTextInputExpanded(!isTextInputExpanded)}
            />

            {/* Ingredients List */}
            <div>
              <h3 className="text-sm font-semibold text-sand-900 mb-3">
                Your Ingredients
              </h3>
              <IngredientList
                ingredients={session?.ingredients || []}
                onUpdate={handleUpdateIngredient}
                onDelete={handleDeleteIngredient}
              />
            </div>

            {/* Re-search Button */}
            <button
              onClick={handleSearchRecipes}
              disabled={
                isSearching ||
                !session ||
                session.ingredients.length === 0 ||
                isProcessing
              }
              className="w-full px-6 py-3 bg-terra-500 text-white rounded-lg font-semibold hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {isSearching ? (
                <>
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
                  Searching recipes...
                </>
              ) : (
                <>
                  <svg
                    className="w-5 h-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Re-search Recipes
                </>
              )}
            </button>
          </div>
        </CollapsibleSection>

        {/* Recipe Search Progress */}
        {(isSearching || searchComplete || searchError) && (
          <RecipeSearchProgress
            currentProgress={searchProgress}
            isComplete={searchComplete}
            error={searchError}
          />
        )}

        {/* Section 2: Recipes */}
        {recipes.length > 0 && (
          <CollapsibleSection
            title={`§ Recipes Found (${recipes.length})`}
            defaultExpanded={true}
          >
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {recipes.map((sr) => (
                  <div
                    key={sr.recipe.id}
                    className="bg-white border border-sand-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                  >
                    <div className="flex gap-3">
                      {sr.recipe.thumbnail_url && (
                        <img
                          src={sr.recipe.thumbnail_url}
                          alt={sr.recipe.title}
                          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <a
                          href={sr.recipe.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm font-medium text-terra-700 hover:underline line-clamp-2 block mb-1"
                        >
                          {sr.recipe.title}
                        </a>
                        <p className="text-xs text-sand-600">
                          {sr.recipe.creator_name} ·{' '}
                          {Math.round(sr.coverage_score * 100)}% match
                        </p>
                        {sr.missing_ingredients.length > 0 && (
                          <p className="text-xs text-chili-600 mt-1">
                            Need: {sr.missing_ingredients.slice(0, 2).join(', ')}
                            {sr.missing_ingredients.length > 2 &&
                              ` +${sr.missing_ingredients.length - 2}`}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Search Again Button */}
              <button
                onClick={handleSearchRecipes}
                disabled={isSearching || !session}
                className="w-full px-6 py-3 bg-white border-2 border-terra-500 text-terra-700 rounded-lg font-semibold hover:bg-terra-50 transition-colors disabled:bg-sand-100 disabled:border-sand-300 disabled:text-sand-500 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                Search Again
              </button>
            </div>
          </CollapsibleSection>
        )}

        {/* Section 3: Meal Plan */}
        {recipes.length > 0 && (
          <CollapsibleSection title="§ Your Meal Plan" defaultExpanded={true}>
            <div className="space-y-6">
              {/* Day Toggles */}
              <div>
                <h3 className="text-sm font-semibold text-sand-900 mb-3">
                  Which days would you like to plan?
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2">
                  {ALL_DAYS.map((day) => {
                    const isEnabled = enabledDays.has(day);
                    const dayLabel = day.charAt(0).toUpperCase() + day.slice(1);

                    return (
                      <button
                        key={day}
                        onClick={() => toggleDay(day)}
                        className={`p-3 rounded-lg border-2 transition-all text-sm font-medium ${
                          isEnabled
                            ? 'border-terra-500 bg-terra-50 text-terra-700'
                            : 'border-sand-200 bg-white text-sand-500 hover:border-sand-300'
                        }`}
                      >
                        {dayLabel}
                        {isEnabled && (
                          <svg
                            className="w-4 h-4 mx-auto mt-1 text-terra-500"
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
              </div>

              {/* Meal Cards */}
              {plan && (
                <div className="space-y-3">
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
                      <ExpandableMealCard
                        key={slot.id}
                        slot={slot}
                        recipe={
                          slot.recipe_id ? recipeMap.get(slot.recipe_id) : undefined
                        }
                      />
                    ))}
                </div>
              )}

              {/* Generate/Regenerate Plan Button */}
              <button
                onClick={handleGeneratePlan}
                disabled={
                  isGeneratingPlan || enabledDays.size === 0 || recipes.length === 0
                }
                className="w-full px-6 py-3 bg-terra-500 text-white rounded-lg font-semibold hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isGeneratingPlan ? (
                  <>
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
                    Generating plan...
                  </>
                ) : (
                  <>
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                    {plan ? 'Regenerate Plan' : 'Generate Plan'}
                  </>
                )}
              </button>
            </div>
          </CollapsibleSection>
        )}
      </main>

      {/* Chat FAB - only show when plan exists */}
      {plan && (
        <>
          <ChatFAB onClick={() => setIsChatOpen(true)} isVisible={!isChatOpen} />

          {/* Mobile: Bottom Sheet */}
          <ChatBottomSheet
            isOpen={isChatOpen}
            onClose={() => setIsChatOpen(false)}
            messages={chatMessages}
            onSendMessage={handleSendChatMessage}
            isLoading={isChatLoading}
          />

          {/* Desktop: Sidebar (hidden on mobile via lg: classes) */}
          <div
            className={`hidden lg:block fixed top-0 right-0 h-screen w-80 bg-white border-l border-sand-200 shadow-2xl transition-transform z-40 ${
              isChatOpen ? 'translate-x-0' : 'translate-x-full'
            }`}
          >
            <ChatPanel
              messages={chatMessages}
              onSendMessage={handleSendChatMessage}
              isLoading={isChatLoading}
            />
            <button
              onClick={() => setIsChatOpen(false)}
              className="absolute top-4 right-4 p-2 text-sand-600 hover:bg-sand-100 rounded-full transition-colors"
              aria-label="Close chat"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
