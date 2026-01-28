import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  SessionStartModal,
  VoiceInputController,
  TextInputFallback,
  IngredientList,
  ConfirmationFooter,
  RecipeSearchProgress,
  ChannelBanner,
} from '../components';
import { authApi, ingredientsApi, streamRecipeSearch, tokenManager, creatorsApi } from '../api';
import type { Ingredient, IngredientSession, ProgressEvent, ScoredRecipe } from '../types';

/**
 * IngredientCollectionPage Component
 *
 * Main page for ingredient collection workflow.
 * Handles session management, voice/text input, ingredient CRUD, and confirmation.
 *
 * Flow:
 * 1. Check for existing session on mount
 * 2. Show SessionStartModal if session exists
 * 3. Allow voice/text input to add ingredients
 * 4. Display ingredients in list with edit/delete
 * 5. Confirm and move to meal planning
 *
 * Features:
 * - Session lifecycle management
 * - Voice and text input modes
 * - Real-time ingredient parsing
 * - Ingredient CRUD operations
 * - Confirmation flow
 */
export function IngredientCollectionPage() {
  // Session state
  const [session, setSession] = useState<IngredientSession | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [existingSession, setExistingSession] = useState<IngredientSession | null>(null);

  // UI state
  const [isTextInputExpanded, setIsTextInputExpanded] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Recipe search state
  const [isSearching, setIsSearching] = useState(false);
  const [searchProgress, setSearchProgress] = useState<ProgressEvent | null>(null);
  const [searchComplete, setSearchComplete] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<ScoredRecipe[]>([]);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Channel banner state
  const [bannerDismissed, setBannerDismissed] = useState(() =>
    localStorage.getItem('channelBannerDismissed') === 'true'
  );

  const { data: creators = [] } = useQuery({
    queryKey: ['creators'],
    queryFn: creatorsApi.getCreators,
    enabled: !bannerDismissed,
  });

  const showBanner = !bannerDismissed && creators.length === 0;

  const handleDismissBanner = () => {
    localStorage.setItem('channelBannerDismissed', 'true');
    setBannerDismissed(true);
  };

  // For demo purposes, use a hardcoded user ID
  // In production, this would come from auth context
  const USER_ID = 'demo-user';

  /**
   * Initialize auth token and check for existing session on mount
   */
  useEffect(() => {
    initializeAuth();
  }, []);

  /**
   * Cleanup: abort streaming on unmount
   */
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const initializeAuth = async (retryCount = 0) => {
    try {
      // Ensure we have a valid token
      await ensureValidToken();

      // Once authenticated, check for existing session
      await checkExistingSession();
    } catch (err: any) {
      console.error('Failed to initialize auth:', err);

      // If we get a 401 and haven't retried yet, clear token and retry once
      if (err.response?.status === 401 && retryCount === 0) {
        console.log('Token invalid, getting fresh token and retrying...');
        tokenManager.clearToken();
        return initializeAuth(1);
      }

      setError('Failed to authenticate. Please refresh and try again.');
    }
  };

  const ensureValidToken = async () => {
    const existingToken = tokenManager.getToken();
    if (!existingToken) {
      // Get a token for the demo user
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
        // No existing session or session is completed, create new
        await createNewSession();
      }
    } catch (err: any) {
      console.error('Failed to check existing session:', err);

      // If it's an auth error (401), let it bubble up to trigger token refresh
      if (err.response?.status === 401) {
        throw err;
      }

      // For other errors (like 404), try to create new session
      await createNewSession();
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await ingredientsApi.createSession(USER_ID);
      setSession(newSession);
    } catch (err: any) {
      console.error('Failed to create session:', err);

      // If it's an auth error (401), let it bubble up to trigger token refresh
      if (err.response?.status === 401) {
        throw err;
      }

      setError('Failed to start session. Please refresh and try again.');
    }
  };

  /**
   * Handle modal actions
   */
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

  /**
   * Parse text input into ingredients and add to session
   */
  const handleTextInput = async (text: string) => {
    if (!session) {
      setError('No active session. Please refresh the page.');
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Parse the text
      const parseResult = await ingredientsApi.parse(text);

      // Add parsed ingredients to session
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

  /**
   * Handle voice transcript (same as text input)
   */
  const handleVoiceTranscript = async (transcript: string) => {
    await handleTextInput(transcript);
  };

  /**
   * Handle wake word detection (stop listening action)
   */
  const handleWakeWord = () => {
    // Wake word detected, voice input will stop automatically
    // This is just a notification, no action needed
    console.log('Wake word detected');
  };

  /**
   * Update an ingredient
   */
  const handleUpdateIngredient = async (id: string, updates: Partial<Ingredient>) => {
    if (!session) return;

    // Optimistically update UI
    const updatedIngredients = session.ingredients.map((ing) =>
      ing.id === id ? { ...ing, ...updates } : ing
    );
    setSession({ ...session, ingredients: updatedIngredients });

    // In a real app, we'd call an API endpoint to persist the update
    // For now, the update is only local
    // TODO: Add backend endpoint for updating individual ingredients
  };

  /**
   * Delete an ingredient
   */
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

  /**
   * Confirm ingredients and start recipe search with streaming progress
   */
  const handleConfirm = async () => {
    if (!session || session.ingredients.length === 0) return;

    setIsProcessing(true);
    setError(null);

    try {
      // First, confirm the session status
      await ingredientsApi.updateStatus(session.id, 'confirmed');
      setIsProcessing(false);

      // Reset search state
      setSearchProgress(null);
      setSearchComplete(false);
      setSearchError(null);
      setSearchResults([]);
      setIsSearching(true);

      // Extract ingredient names
      const ingredientNames = session.ingredients.map((ing) => ing.name);

      // Start streaming recipe search
      const controller = await streamRecipeSearch({
        ingredients: ingredientNames,
        maxResults: 15,
        onProgress: (progress) => {
          setSearchProgress(progress);
        },
        onResult: (recipes) => {
          setSearchResults(recipes);
          setSearchComplete(true);
          setIsSearching(false);
          console.log('Recipe search complete:', recipes);
          // TODO: Navigate to meal planning page with results
        },
        onError: (errorMessage) => {
          setSearchError(errorMessage);
          setIsSearching(false);
        },
      });

      // Store controller for cleanup
      abortControllerRef.current = controller;
    } catch (err) {
      console.error('Failed to confirm ingredients:', err);
      setError('Failed to confirm ingredients. Please try again.');
      setIsProcessing(false);
      setIsSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream bg-kitchen-pattern pb-32">
      {/* Header */}
      <header className="bg-header-gradient shadow-warm-md sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white font-display">What's in your fridge?</h1>
            <p className="text-sm text-terra-50 mt-1">
              Tell me your ingredients and I'll plan your meals
            </p>
          </div>
          <Link
            to="/settings"
            className="p-2 text-white hover:bg-white/10 rounded-full transition-colors"
            aria-label="Settings"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
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
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* Error Display */}
        {error && (
          <div className="bg-chili-50 border-2 border-chili-300 rounded-lg p-4">
            <p className="text-sm text-chili-800">{error}</p>
          </div>
        )}

        {/* Channel Banner */}
        {showBanner && (
          <ChannelBanner onDismiss={handleDismissBanner} />
        )}

        {/* Input Section */}
        <section className="bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6 space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-sand-900 mb-4 text-center">
              Add Ingredients
            </h2>

            {/* Voice Input */}
            <div className="mb-6">
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
          </div>
        </section>

        {/* Ingredients List */}
        <section className="bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6">
          <h2 className="text-lg font-semibold text-sand-900 mb-4">Your Ingredients</h2>
          <IngredientList
            ingredients={session?.ingredients || []}
            onUpdate={handleUpdateIngredient}
            onDelete={handleDeleteIngredient}
          />
        </section>

        {/* Processing Indicator (non-search) */}
        {isProcessing && !isSearching && (
          <div className="flex items-center justify-center py-4">
            <svg
              className="animate-spin h-8 w-8 text-terra-500"
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
          </div>
        )}

        {/* Recipe Search Progress */}
        {(isSearching || searchComplete || searchError) && (
          <RecipeSearchProgress
            currentProgress={searchProgress}
            isComplete={searchComplete}
            error={searchError}
          />
        )}

        {/* Recipe Search Results */}
        {searchResults.length > 0 && (
          <section className="bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6">
            <h2 className="text-lg font-semibold text-sand-900 mb-4">
              Found {searchResults.length} recipes
            </h2>
            <ul className="space-y-4">
              {searchResults.map((sr) => (
                <li key={sr.recipe.id} className="flex gap-4 items-start">
                  {sr.recipe.thumbnail_url && (
                    <img
                      src={sr.recipe.thumbnail_url}
                      alt={sr.recipe.title}
                      className="w-24 h-16 object-cover rounded-lg flex-shrink-0"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <a
                      href={sr.recipe.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-terra-700 hover:underline line-clamp-2"
                    >
                      {sr.recipe.title}
                    </a>
                    <p className="text-xs text-sand-600 mt-1">
                      {sr.recipe.creator_name} &middot;{' '}
                      {Math.round(sr.coverage_score * 100)}% match
                    </p>
                    {sr.missing_ingredients.length > 0 && (
                      <p className="text-xs text-chili-600 mt-0.5">
                        Need: {sr.missing_ingredients.join(', ')}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>

      {/* Confirmation Footer */}
      <ConfirmationFooter
        ingredientCount={session?.ingredients.length || 0}
        onConfirm={handleConfirm}
        isLoading={isProcessing || isSearching}
      />
    </div>
  );
}
