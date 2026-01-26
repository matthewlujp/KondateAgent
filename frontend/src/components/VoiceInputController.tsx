import { useVoiceInput } from '../hooks/useVoiceInput';

interface VoiceInputControllerProps {
  onTranscript: (transcript: string) => void;
  onWakeWord: () => void;
}

/**
 * VoiceInputController Component
 *
 * Microphone button with pulsing animation when listening.
 * Shows error messages and fallback for unsupported browsers.
 *
 * Features:
 * - Large touch-friendly microphone button
 * - Pulsing red animation when actively listening
 * - Error display with user-friendly messages
 * - Browser support detection
 * - Wake word detection for stopping
 */
export function VoiceInputController({ onTranscript, onWakeWord }: VoiceInputControllerProps) {
  const { isListening, isSupported, error, startListening, stopListening } = useVoiceInput({
    onTranscript,
    onWakeWord,
  });

  if (!isSupported) {
    return (
      <div className="bg-saffron-50 border-2 border-saffron-300 rounded-lg p-4 text-center">
        <p className="text-sm text-saffron-800">
          Voice input is not supported in this browser. Please use Chrome, Edge, or Safari, or use
          the text input below.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center space-y-4">
      <div className="relative">
        <button
          onClick={isListening ? stopListening : startListening}
          className={`
            relative w-24 h-24 rounded-full flex items-center justify-center
            transition-all duration-200
            ${
              isListening
                ? 'bg-voice-listening shadow-warm-lg animate-voice-pulse'
                : 'bg-voice-idle shadow-warm-md hover:shadow-warm-lg'
            }
          `}
          aria-label={isListening ? 'Stop listening' : 'Start listening'}
        >
        {isListening ? (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
            />
          </svg>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-12 w-12 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          </svg>
        )}
        </button>

        {/* Radiating rings when listening */}
        {isListening && (
          <>
            <span className="absolute inset-0 rounded-full border-4 border-chili-400 animate-voice-ring pointer-events-none" />
            <span className="absolute inset-0 rounded-full border-4 border-chili-400 animate-voice-ring pointer-events-none" style={{ animationDelay: '0.5s' }} />
          </>
        )}
      </div>

      <div className="text-center">
        {isListening ? (
          <div>
            <p className="text-lg font-medium text-sand-900">Listening...</p>
            <p className="text-sm text-sand-600 mt-1">
              Say "done" or "that's it" when finished
            </p>
          </div>
        ) : (
          <div>
            <p className="text-lg font-medium text-sand-900">Tap to start</p>
            <p className="text-sm text-sand-600 mt-1">
              Tell me what's in your fridge
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="bg-chili-50 border-2 border-chili-300 rounded-lg p-4 text-center max-w-md">
          <p className="text-sm text-chili-800">{error}</p>
        </div>
      )}
    </div>
  );
}
