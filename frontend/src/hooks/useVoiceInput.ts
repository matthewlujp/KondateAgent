import { useState, useEffect, useCallback, useRef } from 'react';

export interface UseVoiceInputOptions {
  onTranscript?: (transcript: string) => void;
  onWakeWord?: () => void;
  language?: string;
  wakeWords?: string[];
}

export interface UseVoiceInputReturn {
  isListening: boolean;
  isSupported: boolean;
  error: string | null;
  startListening: () => void;
  stopListening: () => void;
}

const DEFAULT_WAKE_WORDS = ['done', "that's it", 'that is it', 'finished'];

/**
 * Custom React hook for voice input using Web Speech API
 *
 * Features:
 * - Continuous listening mode
 * - Wake word detection for ending input
 * - Error handling with user-friendly messages
 * - Browser compatibility checking
 *
 * @param options - Configuration options
 * @returns Voice input state and control methods
 */
export function useVoiceInput(options: UseVoiceInputOptions = {}): UseVoiceInputReturn {
  const {
    onTranscript,
    onWakeWord,
    language = 'en-US',
    wakeWords = DEFAULT_WAKE_WORDS,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check browser support on mount
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);

      // Initialize speech recognition
      const recognition = new SpeechRecognition();
      recognition.continuous = true; // Continuous listening mode
      recognition.interimResults = true; // Get interim results
      recognition.lang = language;
      recognition.maxAlternatives = 1;

      recognitionRef.current = recognition;
    } else {
      setIsSupported(false);
      setError('Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.');
    }

    // Cleanup on unmount
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [language]);

  // Check for wake words in transcript
  const checkForWakeWords = useCallback(
    (transcript: string): boolean => {
      const lowerTranscript = transcript.toLowerCase().trim();
      return wakeWords.some((word) => lowerTranscript.includes(word.toLowerCase()));
    },
    [wakeWords]
  );

  // Setup recognition event handlers
  useEffect(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;

    const handleResult = (event: Event) => {
      const speechEvent = event as SpeechRecognitionEvent;
      const results = speechEvent.results;
      const lastResult = results[results.length - 1];

      if (lastResult.isFinal) {
        const transcript = lastResult[0].transcript;

        // Check for wake words
        if (checkForWakeWords(transcript)) {
          if (onWakeWord) {
            onWakeWord();
          }
          // Don't pass wake word to transcript handler
          return;
        }

        // Pass transcript to handler
        if (onTranscript) {
          onTranscript(transcript);
        }
      }
    };

    const handleError = (event: Event) => {
      const errorEvent = event as SpeechRecognitionErrorEvent;
      const errorType = errorEvent.error;

      // Map error types to user-friendly messages
      let errorMessage: string;
      switch (errorType) {
        case 'no-speech':
          errorMessage = 'No speech detected. Please try again.';
          break;
        case 'audio-capture':
          errorMessage = 'No microphone found. Please ensure your microphone is connected.';
          break;
        case 'not-allowed':
          errorMessage = 'Microphone permission denied. Please allow microphone access.';
          break;
        case 'network':
          errorMessage = 'Network error occurred. Please check your connection.';
          break;
        case 'aborted':
          errorMessage = 'Speech recognition was aborted.';
          break;
        case 'service-not-allowed':
          errorMessage = 'Speech recognition service is not allowed.';
          break;
        default:
          errorMessage = `Speech recognition error: ${errorType}`;
      }

      setError(errorMessage);
      setIsListening(false);
    };

    const handleEnd = () => {
      setIsListening(false);
    };

    const handleStart = () => {
      setError(null);
      setIsListening(true);
    };

    // Attach event listeners
    recognition.addEventListener('result', handleResult);
    recognition.addEventListener('error', handleError);
    recognition.addEventListener('end', handleEnd);
    recognition.addEventListener('start', handleStart);

    // Cleanup
    return () => {
      recognition.removeEventListener('result', handleResult);
      recognition.removeEventListener('error', handleError);
      recognition.removeEventListener('end', handleEnd);
      recognition.removeEventListener('start', handleStart);
    };
  }, [onTranscript, onWakeWord, checkForWakeWords]);

  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Voice input is not supported in this browser.');
      return;
    }

    if (!recognitionRef.current) {
      setError('Speech recognition is not initialized.');
      return;
    }

    try {
      setError(null);
      recognitionRef.current.start();
    } catch (err) {
      if (err instanceof Error) {
        // Handle "already started" error
        if (err.message.includes('already started')) {
          setError('Voice input is already active.');
        } else {
          setError(`Failed to start voice input: ${err.message}`);
        }
      } else {
        setError('Failed to start voice input.');
      }
    }
  }, [isSupported]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        if (err instanceof Error) {
          setError(`Failed to stop voice input: ${err.message}`);
        } else {
          setError('Failed to stop voice input.');
        }
      }
    }
  }, [isListening]);

  return {
    isListening,
    isSupported,
    error,
    startListening,
    stopListening,
  };
}
