import { useState } from 'react';
import type { KeyboardEvent } from 'react';

interface AddChannelInputProps {
  onAdd: (url: string) => void;
  isLoading: boolean;
  error: string | null;
}

export function AddChannelInput({ onAdd, isLoading, error }: AddChannelInputProps) {
  const [url, setUrl] = useState('');

  const handleSubmit = () => {
    const trimmed = url.trim();
    if (trimmed) {
      onAdd(trimmed);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Note: The parent can clear errors via the error prop.
  // The input value is controlled by local state for simplicity.

  return (
    <div>
      <div className="flex gap-2">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Paste YouTube or Instagram URL"
          disabled={isLoading}
          className="flex-1 px-3 py-2 border border-sand-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-terra-500 disabled:bg-sand-100 disabled:text-sand-500"
        />
        <button
          onClick={handleSubmit}
          disabled={isLoading || !url.trim()}
          className="px-4 py-2 text-sm font-medium text-white bg-terra-500 hover:bg-terra-600 rounded-lg transition-colors disabled:bg-sand-300 disabled:cursor-not-allowed whitespace-nowrap min-w-[110px]"
        >
          {isLoading ? 'Adding...' : 'Add Channel'}
        </button>
      </div>
      {error && (
        <p className="mt-2 text-sm text-chili-600">{error}</p>
      )}
    </div>
  );
}

// Export a helper to allow parent to imperatively clear
export type { AddChannelInputProps };
