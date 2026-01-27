import { Link } from 'react-router-dom';

interface ChannelBannerProps {
  onDismiss: () => void;
}

export function ChannelBanner({ onDismiss }: ChannelBannerProps) {
  return (
    <div className="bg-terra-50 border border-terra-200 rounded-xl p-4 flex items-center justify-between gap-3 animate-slide-up">
      <div className="flex-1">
        <p className="text-sm font-medium text-terra-800">
          Add your favorite recipe channels for personalized results
        </p>
        <Link
          to="/settings"
          className="text-sm font-semibold text-terra-600 hover:text-terra-700 underline mt-1 inline-block"
        >
          Add Channels
        </Link>
      </div>
      <button
        onClick={onDismiss}
        className="p-1.5 text-terra-400 hover:text-terra-600 hover:bg-terra-100 rounded-full transition-colors flex-shrink-0"
        aria-label="Dismiss"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}
