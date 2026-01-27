import type { CreatorSource } from '../types';

export function detectSource(url: string): CreatorSource | null {
  if (!url) return null;

  const lower = url.toLowerCase();

  if (lower.includes('youtube.com/')) return 'youtube';
  if (lower.includes('youtu.be/')) return 'youtube';
  if (lower.includes('instagram.com/')) return 'instagram';

  return null;
}
