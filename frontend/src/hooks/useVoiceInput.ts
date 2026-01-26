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
  const shouldBeListeningRef = useRef(false); // Track if user wants to listen

  // Store callbacks in refs so the event-handler effect doesn't depend on them
  const onTranscriptRef = useRef(onTranscript);
  const onWakeWordRef = useRef(onWakeWord);
  useEffect(() => { onTranscriptRef.current = onTranscript; }, [onTranscript]);
  useEffect(() => { onWakeWordRef.current = onWakeWord; }, [onWakeWord]);

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
          if (onWakeWordRef.current) {
            onWakeWordRef.current();
          }
          // Don't pass wake word to transcript handler
          return;
        }

        // Pass transcript to handler
        if (onTranscriptRef.current) {
          onTranscriptRef.current(transcript);
        }
      }
    };

    const handleError = (event: Event) => {
      const errorEvent = event as SpeechRecognitionErrorEvent;
      const errorType = errorEvent.error;

      // For "no-speech" errors, don't stop - just continue listening
      if (errorType === 'no-speech') {
        // Don't show error, don't stop listening - this is normal
        return;
      }

      // Map error types to user-friendly messages
      let errorMessage: string;
      switch (errorType) {
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
      shouldBeListeningRef.current = false;
    };

    const handleEnd = () => {
      setIsListening(false);

      // Auto-restart if user still wants to listen
      if (shouldBeListeningRef.current && recognitionRef.current) {
        try {
          recognitionRef.current.start();
        } catch (err) {
          // Ignore "already started" errors during restart
          console.log('Restart attempt:', err);
        }
      }
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
  }, [checkForWakeWords]);

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
      shouldBeListeningRef.current = true;
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
    shouldBeListeningRef.current = false;
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
