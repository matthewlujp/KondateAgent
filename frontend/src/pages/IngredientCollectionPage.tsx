import { useState, useEffect } from 'react';
import {
  SessionStartModal,
  VoiceInputController,
  TextInputFallback,
  IngredientList,
  ConfirmationFooter,
} from '../components';
import { ingredientsApi } from '../api';
import type { Ingredient, IngredientSession } from '../types';

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

  // For demo purposes, use a hardcoded user ID
  // In production, this would come from auth context
  const USER_ID = 'demo-user';

  /**
   * Check for existing session on mount
   */
  useEffect(() => {
    checkExistingSession();
  }, []);

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
    } catch (err) {
      console.error('Failed to check existing session:', err);
      // If check fails, create new session anyway
      await createNewSession();
    }
  };

  const createNewSession = async () => {
    try {
      const newSession = await ingredientsApi.createSession(USER_ID);
      setSession(newSession);
    } catch (err) {
      console.error('Failed to create session:', err);
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
   * Confirm ingredients and move to meal planning
   */
  const handleConfirm = async () => {
    if (!session || session.ingredients.length === 0) return;

    setIsProcessing(true);
    setError(null);

    try {
      await ingredientsApi.updateStatus(session.id, 'confirmed');

      // In a real app, navigate to meal planning page
      // For now, just show a success message
      alert('Ingredients confirmed! Ready for meal planning.');

      // Reset to create a new session for next time
      await createNewSession();
    } catch (err) {
      console.error('Failed to confirm ingredients:', err);
      setError('Failed to confirm ingredients. Please try again.');
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-cream bg-kitchen-pattern pb-32">
      {/* Header */}
      <header className="bg-header-gradient shadow-warm-md sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-white font-display">What's in your fridge?</h1>
          <p className="text-sm text-terra-50 mt-1">
            Tell me your ingredients and I'll plan your meals
          </p>
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

        {/* Processing Indicator */}
        {isProcessing && (
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
      </main>

      {/* Confirmation Footer */}
      <ConfirmationFooter
        ingredientCount={session?.ingredients.length || 0}
        onConfirm={handleConfirm}
        isLoading={isProcessing}
      />
    </div>
  );
}
