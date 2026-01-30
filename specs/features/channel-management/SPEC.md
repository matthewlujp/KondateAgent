# Feature: Channel Management

## Purpose

Let users tell us which recipe creators they trust, so we prioritize recipes from those sources.

## User Problem

Generic recipe search returns random results. Users have favorite YouTube channels and Instagram accounts whose cooking style, complexity level, and taste they already know and like.

## Behavior

### Adding Creators

Users can add creators in several ways:
- **During onboarding**: "Add your favorite recipe creators?" prompt
- **In Settings**: Dedicated section for managing creators
- **From results** (future): "Follow this creator" button on meal plans

### How to Add

1. Go to Settings
2. Tap "Add Creator"
3. Paste a YouTube channel URL or Instagram handle
4. System validates and shows creator name/thumbnail
5. Creator added to list

### Supported Formats

**YouTube:**
- `youtube.com/channel/UCxxxxx`
- `youtube.com/@handle`
- `youtube.com/c/ChannelName`

**Instagram:**
- `instagram.com/username`
- `@username`

### Managing Creators

- View all registered creators with thumbnails
- See which platform each is from (YouTube/Instagram badge)
- Tap to remove a creator
- No limit on number of creators

### Effect on Recipes

- Registered creator recipes appear first in search results
- Still includes other creators for variety
- Works silently - users just see better results

## Edge Cases

| Situation | System Response |
|-----------|-----------------|
| Invalid URL | "Couldn't find that channel. Check the URL?" |
| Creator already added | "You've already added this creator" |
| Channel doesn't exist | "Channel not found on YouTube" |
| No creators added | Recipe search still works, just no priority |

## Success Criteria

- Add a creator in under 10 seconds
- Clear visual confirmation of added creator
- Recipes from registered creators appear in meal plans
