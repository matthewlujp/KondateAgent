import { useState } from 'react';
import type { PreferredCreator } from '../types';

interface ChannelCardProps {
  channel: PreferredCreator;
  onDelete: (id: string) => void;
}

export function ChannelCard({ channel, onDelete }: ChannelCardProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  const isYouTube = channel.source === 'youtube';

  const handleDelete = () => {
    onDelete(channel.id);
    setShowConfirm(false);
  };

  return (
    <div className="flex items-center justify-between p-3 rounded-lg border bg-white border-sand-200 shadow-warm hover:shadow-warm-md transition-all animate-slide-up">
      {/* Avatar placeholder */}
      <div className={`w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
        isYouTube ? 'bg-chili-50 text-chili-500' : 'bg-terra-50 text-terra-500'
      }`}>
        <span className="text-xl">{isYouTube ? '▶' : '◎'}</span>
      </div>

      {/* Channel info */}
      <div className="flex-1 min-w-0 ml-3">
        <div className="font-medium text-sand-900 truncate">{channel.creator_name}</div>
        <div className={`text-xs font-medium inline-flex items-center gap-1 mt-0.5 ${
          isYouTube ? 'text-chili-600' : 'text-terra-600'
        }`}>
          {isYouTube ? 'YouTube' : 'Instagram'}
        </div>
      </div>

      {/* Actions */}
      {showConfirm ? (
        <div className="flex items-center gap-2 ml-2 animate-fade-in">
          <span className="text-xs text-sand-700 whitespace-nowrap">
            Remove {channel.creator_name}?
          </span>
          <button
            onClick={() => setShowConfirm(false)}
            className="px-2 py-1 text-xs text-sand-700 bg-sand-100 hover:bg-sand-200 rounded transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            className="px-2 py-1 text-xs text-white bg-chili-500 hover:bg-chili-600 rounded transition-colors"
          >
            Remove
          </button>
        </div>
      ) : (
        <button
          onClick={() => setShowConfirm(true)}
          className="ml-2 p-2 text-sand-400 hover:text-chili-600 hover:bg-chili-50 rounded-full transition-colors"
          aria-label="Delete channel"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      )}
    </div>
  );
}
