import type { CreatorSource } from '../types';

/**
 * Detects the source platform from a creator URL
 * @param url - The URL to analyze
 * @returns The detected source ('youtube' | 'instagram') or null if not recognized
 */
export function detectSource(url: string): CreatorSource | null {
  if (!url) return null;

  try {
    const parsed = new URL(url);
    const hostname = parsed.hostname.toLowerCase().replace(/^www\./, '');

    if (hostname === 'youtube.com' || hostname === 'youtu.be') return 'youtube';
    if (hostname === 'instagram.com') return 'instagram';

    return null;
  } catch {
    // Not a valid URL
    return null;
  }
}
