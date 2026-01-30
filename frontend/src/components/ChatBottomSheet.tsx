import { useState, useEffect, useRef } from 'react';
import type { ChatMessage } from '../types/mealPlan';

interface ChatBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
}

/**
 * ChatBottomSheet Component
 *
 * Mobile-only chat interface that slides up from the bottom of the screen.
 * Provides a modal overlay for meal plan refinement chat on small screens.
 *
 * Features:
 * - Backdrop with tap-to-close
 * - Slides up from bottom with animation
 * - Height 50vh (half screen) for better visibility
 * - Auto-scrolls to bottom on new messages
 * - Auto-focus input on open
 * - Loading indicator with animated dots
 * - Empty state with helpful suggestions
 */
export function ChatBottomSheet({
  isOpen,
  onClose,
  messages,
  onSendMessage,
  isLoading,
}: ChatBottomSheetProps) {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isOpen && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Focus input when sheet opens
  useEffect(() => {
    if (isOpen) {
      // Delay to allow animation to start
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed && !isLoading) {
      onSendMessage(trimmed);
      setInputValue('');
      // Focus back on input after sending
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleBackdropClick = (e: React.MouseEvent) => {
    // Only close if clicking the backdrop itself, not the sheet
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    // Mobile only - hidden on large screens
    <div className="lg:hidden">
      {/* Backdrop */}
      <div
        data-testid="chat-backdrop"
        onClick={handleBackdropClick}
        className="fixed inset-0 bg-black/40 z-40 animate-in fade-in duration-200"
      />

      {/* Bottom Sheet */}
      <div
        data-testid="chat-bottom-sheet"
        className="fixed inset-x-0 bottom-0 z-50 bg-white rounded-t-2xl shadow-2xl h-[50vh] flex flex-col animate-in slide-in-from-bottom duration-300"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-sand-200 bg-terra-50 rounded-t-2xl flex-shrink-0">
          <div>
            <h3 className="text-base font-semibold text-terra-700">
              Refine Your Plan
            </h3>
            <p className="text-xs text-terra-600 mt-0.5">
              Ask to swap meals or make changes
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close chat"
            className="p-2 hover:bg-terra-100 rounded-full transition-colors"
          >
            <svg
              className="w-6 h-6 text-terra-600"
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

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
          {messages.length === 0 ? (
            // Empty state
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="w-12 h-12 bg-terra-100 rounded-full flex items-center justify-center mb-3">
                <svg
                  className="w-6 h-6 text-terra-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                  />
                </svg>
              </div>
              <p className="text-sm text-sand-600 mb-2">
                Your plan is ready!
              </p>
              <p className="text-xs text-sand-500 max-w-xs">
                Try: "Swap Tuesday for something lighter" or "Change Friday to a vegetarian meal"
              </p>
            </div>
          ) : (
            // Message list
            <>
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[85%] rounded-lg px-4 py-2.5 ${
                      message.role === 'user'
                        ? 'bg-terra-500 text-white'
                        : 'bg-sand-100 text-sand-900'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap break-words">
                      {message.content}
                    </p>
                    {message.tool_calls && message.tool_calls.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-sand-200 text-xs text-sand-600">
                        <div className="flex items-center">
                          <svg
                            className="w-3 h-3 mr-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
                            />
                          </svg>
                          Performed {message.tool_calls.length} action(s)
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-sand-100 rounded-lg px-4 py-3">
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-sand-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                      <div className="w-2 h-2 bg-sand-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                      <div className="w-2 h-2 bg-sand-400 rounded-full animate-bounce" />
                    </div>
                  </div>
                </div>
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Form */}
        <div className="p-4 border-t border-sand-200 bg-sand-50 flex-shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask to swap a meal..."
              disabled={isLoading}
              className="flex-1 px-4 py-2.5 border border-sand-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terra-500 disabled:bg-sand-100 disabled:text-sand-500 text-sm"
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="px-5 py-2.5 bg-terra-500 text-white rounded-lg font-medium hover:bg-terra-600 transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed text-sm"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
