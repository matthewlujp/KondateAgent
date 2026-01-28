import { useNavigate } from 'react-router-dom';
import { ChannelManagementSection } from '../components/ChannelManagementSection';
import { PlaceholderSection } from '../components/PlaceholderSection';

export function SettingsPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-cream bg-kitchen-pattern">
      {/* Header */}
      <header className="bg-header-gradient shadow-warm-md sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="p-2 -ml-2 text-white hover:bg-white/10 rounded-full transition-colors"
            aria-label="Go back"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-2xl font-bold text-white font-display">Settings</h1>
            <p className="text-sm text-terra-50 mt-0.5">Manage your preferences</p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        <ChannelManagementSection />

        <PlaceholderSection
          title="Dietary Preferences"
          description="Set dietary restrictions and preferences"
        />

        <PlaceholderSection
          title="Meal Planning"
          description="Configure default meal plan settings"
        />
      </main>
    </div>
  );
}
