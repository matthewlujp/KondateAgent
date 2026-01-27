import { describe, it, expect } from 'vitest';
import { detectSource } from '../../utils/detectSource';

describe('detectSource', () => {
  it('detects youtube.com/@handle', () => {
    expect(detectSource('https://www.youtube.com/@BabishCulinaryUniverse')).toBe('youtube');
  });

  it('detects youtube.com/c/channel', () => {
    expect(detectSource('https://youtube.com/c/JoshuaWeissman')).toBe('youtube');
  });

  it('detects youtube.com/channel/UCxxxx', () => {
    expect(detectSource('https://youtube.com/channel/UC123456')).toBe('youtube');
  });

  it('detects instagram.com/username', () => {
    expect(detectSource('https://www.instagram.com/foodblogger')).toBe('instagram');
  });

  it('detects instagram.com/username/ with trailing slash', () => {
    expect(detectSource('https://instagram.com/foodblogger/')).toBe('instagram');
  });

  it('returns null for unrecognized URLs', () => {
    expect(detectSource('https://www.tiktok.com/@someone')).toBeNull();
  });

  it('returns null for empty string', () => {
    expect(detectSource('')).toBeNull();
  });

  it('returns null for non-URL text', () => {
    expect(detectSource('not a url')).toBeNull();
  });
});
