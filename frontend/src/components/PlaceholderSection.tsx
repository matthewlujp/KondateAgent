interface PlaceholderSectionProps {
  title: string;
  description: string;
}

export function PlaceholderSection({ title, description }: PlaceholderSectionProps) {
  return (
    <section className="bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6 opacity-60">
      <div className="flex items-center gap-2 mb-2">
        <h2 className="text-lg font-semibold text-sand-700">{title}</h2>
        <span className="px-2 py-0.5 text-xs font-medium text-sand-600 bg-sand-200 rounded-full">
          Coming soon
        </span>
      </div>
      <p className="text-sm text-sand-500">{description}</p>
    </section>
  );
}
