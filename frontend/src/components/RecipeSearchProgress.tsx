import type { ProgressEvent } from '../types';

interface RecipeSearchProgressProps {
  currentProgress: ProgressEvent | null;
  isComplete: boolean;
  error: string | null;
}

/**
 * RecipeSearchProgress Component
 *
 * Displays a 5-step progress indicator for recipe search pipeline.
 * Shows checkmarks for completed steps, spinner for active step,
 * and empty circles for pending steps.
 *
 * Features:
 * - Vertical step layout with connecting lines
 * - Color-coded states: herb (done), terra (active), sand (pending)
 * - Error state with chili-themed message
 * - Smooth transitions between states
 */
export function RecipeSearchProgress({
  currentProgress,
  isComplete,
  error,
}: RecipeSearchProgressProps) {
  const steps = [
    { step: 1, phase: 'generating_queries', label: 'Generating search queries' },
    { step: 2, phase: 'searching_platforms', label: 'Searching platforms' },
    { step: 3, phase: 'parsing_recipes', label: 'Parsing recipe descriptions' },
    { step: 4, phase: 'scoring', label: 'Scoring ingredient matches' },
    { step: 5, phase: 'finalizing', label: 'Finalizing results' },
  ];

  const currentStep = currentProgress?.step || 0;

  const getStepStatus = (stepNumber: number): 'done' | 'active' | 'pending' => {
    if (isComplete || stepNumber < currentStep) return 'done';
    if (stepNumber === currentStep) return 'active';
    return 'pending';
  };

  return (
    <div className="my-6 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Error State */}
        {error && (
          <div className="mb-4 p-4 bg-chili-50 border border-chili-200 rounded-lg">
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-chili-500 mt-0.5 mr-3 flex-shrink-0"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <h4 className="text-sm font-semibold text-chili-800 mb-1">
                  Search Failed
                </h4>
                <p className="text-sm text-chili-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Progress Steps */}
        <div className="space-y-1">
          {steps.map((step, index) => {
            const status = getStepStatus(step.step);
            const isLast = index === steps.length - 1;
            const showMessage = status === 'active' && currentProgress?.message;

            return (
              <div key={step.step} className="relative">
                {/* Connecting Line */}
                {!isLast && (
                  <div
                    className={`absolute left-4 top-8 w-0.5 h-6 transition-colors ${
                      status === 'done' ? 'bg-herb-300' : 'bg-sand-200'
                    }`}
                  />
                )}

                {/* Step Row */}
                <div className="flex items-start">
                  {/* Step Indicator */}
                  <div className="relative flex-shrink-0">
                    {status === 'done' ? (
                      // Done: Checkmark
                      <div className="w-8 h-8 rounded-full bg-herb-500 flex items-center justify-center">
                        <svg
                          className="w-5 h-5 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    ) : status === 'active' ? (
                      // Active: Spinner
                      <div className="w-8 h-8 rounded-full border-2 border-terra-500 border-t-transparent animate-spin" />
                    ) : (
                      // Pending: Empty circle
                      <div className="w-8 h-8 rounded-full border-2 border-sand-300 bg-white" />
                    )}
                  </div>

                  {/* Step Label */}
                  <div className="ml-4 flex-1 min-w-0">
                    <p
                      className={`text-sm font-medium transition-colors ${
                        status === 'done'
                          ? 'text-herb-700'
                          : status === 'active'
                          ? 'text-terra-700'
                          : 'text-sand-500'
                      }`}
                    >
                      {step.label}
                    </p>
                    {showMessage && (
                      <p className="text-xs text-terra-600 mt-1 animate-pulse">
                        {currentProgress.message}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Completion Message */}
        {isComplete && !error && (
          <div className="mt-4 p-3 bg-herb-50 border border-herb-200 rounded-lg">
            <p className="text-sm text-herb-700 text-center font-medium">
              Recipe search complete!
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
