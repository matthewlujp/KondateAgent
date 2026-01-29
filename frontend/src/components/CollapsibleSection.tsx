import { useState, ReactNode } from 'react';

interface CollapsibleSectionProps {
  title: string;
  children: ReactNode;
  defaultExpanded?: boolean;
}

export function CollapsibleSection({
  title,
  children,
  defaultExpanded = true,
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <section className="bg-white border border-sand-200 rounded-xl shadow-warm overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-6 py-4 flex items-center justify-between bg-sand-50 hover:bg-sand-100 transition-colors"
        aria-expanded={isExpanded}
      >
        <h2 className="text-lg font-semibold text-sand-900">{title}</h2>
        <svg
          className={`w-5 h-5 text-sand-600 transition-transform ${
            isExpanded ? 'rotate-180' : ''
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* Content */}
      <div
        className="p-6"
        style={{ display: isExpanded ? 'block' : 'none' }}
      >
        {children}
      </div>
    </section>
  );
}
