# Channel Management UI Design

**Date:** 2026-01-27
**Feature:** Frontend UI for Managing Favorite Recipe Channels
**Status:** Design Complete, Ready for Implementation

## Overview

Implement a frontend UI for users to manage their favorite recipe sources (YouTube channels and Instagram accounts). This feature enables users to configure which creators' recipes should be prioritized in the recipe collection system.

## Context

The backend API for channel management already exists (`/api/creators`), supporting:
- List user's preferred creators (GET)
- Add new creator (POST)
- Delete creator (DELETE)

The backend uses an in-memory store and validates/parses YouTube and Instagram URLs. This design focuses solely on the frontend implementation.

## Design Decisions

### 1. Navigation & Routing

**New Routes:**
- `/` - IngredientCollectionPage (existing, becomes index route)
- `/settings` - New SettingsPage for channel management

**Navigation Pattern:**
- Settings icon (gear/cog) added to IngredientCollectionPage header (top-right)
- Back button (← arrow) on SettingsPage header to return to home
- Links to settings from dismissible banner (when no channels configured)

**Router Implementation:**
- Add React Router (`react-router-dom`)
- Wrap App in `<BrowserRouter>`
- Use `<Routes>` with two `<Route>` elements

### 2. User Flow

**Onboarding (Optional, Non-Blocking):**
- On IngredientCollectionPage, if user has no channels configured: show dismissible banner
- Banner text: "Add your favorite recipe channels for personalized results"
- Banner links to `/settings`
- Dismissal tracked in localStorage (`channelBannerDismissed`)
- User can proceed with ingredient collection without configuring channels

**Settings Access:**
- Always available via settings icon in header
- Users can add/remove channels at any time

**Adding Channels:**
1. User pastes YouTube or Instagram URL in single input field
2. System auto-detects platform type (backend handles this)
3. Loading state during API call
4. On success: channel appears in list, input clears
5. On error: error message shown below input, input retains value for correction

**Deleting Channels:**
1. User clicks delete (trash icon) on channel card
2. Inline confirmation appears: "Remove [Channel Name]?" with Cancel/Confirm
3. On confirm: optimistic removal (immediate UI update)
4. If API fails: roll back and show error

### 3. Settings Page Structure

**Layout:**
- Same visual design as IngredientCollectionPage
- Warm header with gradient (`bg-header-gradient`)
- Kitchen-pattern background (`bg-cream bg-kitchen-pattern`)
- Max-width container (`max-w-2xl mx-auto`)

**Settings Sections (Multi-section with placeholders):**

1. **Favorite Channels** (Fully Implemented)
   - Active section with full functionality
   - Add channel input at top
   - List of configured channels below
   - Empty state when no channels

2. **Dietary Preferences** (Placeholder)
   - Card with "Coming soon" badge
   - Description: "Set dietary restrictions and preferences"
   - Grayed out/disabled appearance

3. **Meal Planning** (Placeholder)
   - Card with "Coming soon" badge
   - Description: "Configure default meal plan settings"
   - Grayed out/disabled appearance

**Visual Consistency:**
- Each section: `bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6`
- Maintains design language from IngredientCollectionPage
- Uses existing color palette: terra (primary), sand (backgrounds), chili (errors)

### 4. Channel Management Interface

**Add Channel Input:**
- Single text input with placeholder: "Paste YouTube or Instagram URL"
- "Add Channel" button (or Enter key submits)
- Loading spinner replaces button text during API call
- Error display below input for validation failures
- Auto-clear on success

**Supported URL Formats:**
- YouTube: `youtube.com/@channelname`, `youtube.com/c/channelname`, `youtube.com/channel/UCxxxxx`
- Instagram: `instagram.com/username`

**Channel List:**
- Minimal card layout (scannable, clean)
- Each card contains:
  - **Left**: Circular avatar/thumbnail (48x48px)
  - **Center**:
    - Channel name (bold, truncated if long)
    - Platform badge (YouTube 📺 or Instagram 📷 icon + text)
  - **Right**: Delete button (trash icon, red on hover)
- Spacing: 12px padding, 8px gap between cards
- Cards use same styling as ingredient items

**Empty State:**
- Centered icon (📺 or custom illustration)
- "No channels yet"
- Subtitle: "Add your first channel to get personalized recipe recommendations"
- Muted colors (sand-600)

**Delete Confirmation:**
- Inline confirmation on card
- Two buttons: Cancel (gray) / Confirm (red)
- Prevents accidental deletion

### 5. API Integration

**New API Client (`src/api/creators.ts`):**
```typescript
interface PreferredCreator {
  id: string;
  user_id: string;
  source: 'youtube' | 'instagram';
  creator_id: string;
  creator_name: string;
  added_at: string;
}

interface AddCreatorRequest {
  source: 'youtube' | 'instagram';
  url: string;
}

export const creatorsApi = {
  getCreators: () => Promise<PreferredCreator[]>,
  addCreator: (request: AddCreatorRequest) => Promise<PreferredCreator>,
  deleteCreator: (creatorId: string) => Promise<void>
}
```

**Type Definitions (`src/types/creator.ts`):**
```typescript
export type CreatorSource = 'youtube' | 'instagram';

export interface PreferredCreator {
  id: string;
  user_id: string;
  source: CreatorSource;
  creator_id: string;
  creator_name: string;
  added_at: string;
}
```

**State Management (React Query):**
- `useQuery(['creators'])` - Fetch and cache channel list
- `useMutation(addCreator)` - Add channel with optimistic updates
- `useMutation(deleteCreator)` - Delete channel with optimistic updates
- Leverages existing React Query configuration in `App.tsx`
- Automatic refetching, error retry, caching already configured

**Banner State (localStorage):**
- Key: `'channelBannerDismissed'`
- Check on IngredientCollectionPage mount
- Show banner if: not dismissed AND no channels configured
- Set flag on dismiss click

**Authentication:**
- Uses existing `tokenManager` and JWT Bearer token pattern
- All creator API calls include `Authorization: Bearer <token>` header
- Token refresh on 401 handled by existing pattern from IngredientCollectionPage

### 6. Error Handling

**API Error Scenarios:**

| Error | Status | User Message | Behavior |
|-------|--------|--------------|----------|
| Invalid URL | 400 | "Invalid URL format. Please enter a valid YouTube or Instagram link." | Input retains value for correction |
| Channel Not Found | 404 | "Channel not found. Please check the URL and try again." | Input retains value for correction |
| Duplicate Channel | 409 | "You've already added this channel." | Auto-clear input |
| Network/Server Error | 500/Network | "Something went wrong. Please try again." | Show retry button |
| Authentication Error | 401 | (Silent) | Auto-refresh token, retry request |

**Loading States:**
- Add button: Show spinner, disable during API call
- Delete button: Show spinner, disable during API call
- Initial load: Skeleton cards (3 shimmer placeholders)
- Prevent double-submission during mutations

**Optimistic Updates:**
- Add: Channel appears immediately in list
- Delete: Channel removed immediately from list
- Roll back on API failure with error notification
- React Query handles optimistic update logic

**Validation:**
- Client-side: Check URL is not empty
- Server-side: Backend validates URL format and channel existence
- Show server validation errors below input

### 7. Component Architecture

**Component Hierarchy:**
```
App (with BrowserRouter)
└── Routes
    ├── Route "/" → IngredientCollectionPage (updated)
    │   ├── Header (with settings icon)
    │   ├── ChannelBanner (conditional)
    │   └── ... existing components
    └── Route "/settings" → SettingsPage (new)
        ├── Header (with back button)
        ├── ChannelManagementSection
        │   ├── AddChannelInput
        │   └── ChannelList
        │       └── ChannelCard (multiple)
        ├── PlaceholderSection (Dietary)
        └── PlaceholderSection (Meal Planning)
```

**New Components:**

1. **`SettingsPage.tsx`** (Page Component)
   - Container for all settings sections
   - Header with back navigation (useNavigate)
   - Renders ChannelManagementSection + placeholders
   - Overall page layout and spacing

2. **`ChannelManagementSection.tsx`** (Feature Component)
   - React Query hooks: useQuery, useMutation
   - Manages channel list state
   - Handles add/delete operations
   - Error boundary for API failures
   - Renders AddChannelInput + ChannelList

3. **`AddChannelInput.tsx`** (Input Component)
   - Controlled input (local state)
   - Submit handler (calls parent callback)
   - Loading and error states
   - Form validation (non-empty)
   - Enter key submission

4. **`ChannelCard.tsx`** (List Item Component)
   - Displays channel info (avatar, name, badge)
   - Platform icon (YouTube/Instagram)
   - Delete button with confirmation state
   - Accepts `onDelete` callback
   - 44px minimum touch target

5. **`ChannelBanner.tsx`** (Banner Component)
   - Conditional rendering (no channels + not dismissed)
   - Link to `/settings` (react-router Link)
   - Close button (X icon)
   - localStorage persistence on dismiss
   - Warm, inviting design (terra colors)

6. **`PlaceholderSection.tsx`** (Reusable Component)
   - Takes title, description props
   - "Coming soon" badge
   - Disabled/grayed appearance
   - Used for future settings sections

**Component Props:**

```typescript
// AddChannelInput
interface AddChannelInputProps {
  onAdd: (url: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

// ChannelCard
interface ChannelCardProps {
  channel: PreferredCreator;
  onDelete: (id: string) => Promise<void>;
}

// ChannelBanner
interface ChannelBannerProps {
  onDismiss: () => void;
}

// PlaceholderSection
interface PlaceholderSectionProps {
  title: string;
  description: string;
}
```

### 8. Styling & Design System

**Color Palette (Existing):**
- Primary: `terra-*` (warm terracotta)
- Backgrounds: `sand-*` (warm cream/beige)
- Errors: `chili-*` (warm red)
- Kitchen pattern background

**Key Styles:**
- Headers: `bg-header-gradient shadow-warm-md`
- Cards: `bg-sand-50 border border-sand-200 rounded-xl shadow-warm p-6`
- Buttons: `bg-terra-500 hover:bg-terra-600 text-white rounded-lg px-4 py-2`
- Icons: Size 20-24px, terra-500 color
- Touch targets: Minimum 44x44px for mobile

**Responsive Design:**
- Mobile-first approach (existing pattern)
- Max-width containers: `max-w-2xl mx-auto`
- Touch-friendly spacing and targets
- Test on viewport widths: 320px, 375px, 428px

**Icons:**
- Settings: Gear/cog icon (⚙️ or SVG)
- Back: Left arrow (← or SVG)
- Delete: Trash can (🗑️ or SVG)
- YouTube: 📺 emoji or custom SVG
- Instagram: 📷 emoji or custom SVG
- Close: X icon (✕ or SVG)

**Animations:**
- Spinner: Existing pattern from IngredientCollectionPage
- Card hover: Subtle scale or shadow transition
- Button hover: Background color transition
- Keep animations subtle and performant

### 9. Testing Strategy

**Component Tests (React Testing Library):**

1. **AddChannelInput**
   - Input changes update local state
   - Form submission calls onAdd callback
   - Loading state disables input and shows spinner
   - Error message displays when error prop set
   - Enter key triggers submission

2. **ChannelCard**
   - Renders channel name, platform badge correctly
   - Delete button shows confirmation on click
   - Confirmation buttons call onDelete / cancel
   - Platform icons render for YouTube vs Instagram

3. **ChannelManagementSection**
   - Fetches channels on mount
   - Empty state shows when no channels
   - Add channel mutation updates list optimistically
   - Delete channel mutation updates list optimistically
   - API errors show error messages

4. **ChannelBanner**
   - Renders when conditions met (no channels, not dismissed)
   - Dismiss button calls onDismiss callback
   - Link to settings page present

5. **SettingsPage**
   - Renders all sections
   - Back button navigates to home
   - Placeholder sections render correctly

**Integration Tests:**

1. **Full Add Flow**
   - Enter URL → Submit → Loading → Success → List updates
   - Mock API response with channel data
   - Verify optimistic update + actual update

2. **Full Delete Flow**
   - Click delete → Confirm → Loading → Success → List updates
   - Verify optimistic update + actual update

3. **Error Scenarios**
   - Invalid URL (400) → Error message shown
   - Duplicate channel (409) → Error message shown
   - Network error → Error message + retry option

4. **Token Refresh**
   - 401 response triggers token refresh
   - Request retried after refresh
   - Falls back to re-auth if refresh fails

**Manual Testing Checklist:**

- [ ] Settings icon visible and clickable on mobile
- [ ] Banner shows when no channels configured
- [ ] Banner dismissal persists across page reloads
- [ ] Banner disappears after adding first channel
- [ ] Add valid YouTube URL → Success
- [ ] Add valid Instagram URL → Success
- [ ] Add invalid URL → Error message
- [ ] Add duplicate channel → Error message
- [ ] Delete channel → Confirmation → Success
- [ ] Delete channel → Cancel → No action
- [ ] Long channel names truncate properly
- [ ] All touch targets meet 44px minimum
- [ ] Navigation works (home ↔ settings)
- [ ] Back button returns to ingredient page
- [ ] Responsive on 320px, 375px, 428px widths

### 10. Implementation Order

**Phase 1: Setup & Types**
1. Install `react-router-dom`
2. Create `src/types/creator.ts` with type definitions
3. Create `src/api/creators.ts` with API client
4. Update `src/api/index.ts` to export creatorsApi

**Phase 2: Static Components**
5. Create `PlaceholderSection.tsx` (simple, no state)
6. Create `ChannelCard.tsx` (display only, test with mock data)
7. Test ChannelCard in isolation

**Phase 3: Interactive Components**
8. Create `AddChannelInput.tsx` (controlled input, callbacks)
9. Test AddChannelInput in isolation
10. Create `ChannelManagementSection.tsx` (React Query integration)
11. Test ChannelManagementSection with mocked API

**Phase 4: Page Assembly**
12. Create `SettingsPage.tsx` (assemble all sections)
13. Test SettingsPage rendering

**Phase 5: Routing**
14. Update `App.tsx` to add BrowserRouter and Routes
15. Move IngredientCollectionPage to index route
16. Add settings route
17. Test navigation

**Phase 6: Navigation Elements**
18. Add settings icon to IngredientCollectionPage header
19. Test settings icon navigation
20. Create `ChannelBanner.tsx`
21. Add banner to IngredientCollectionPage (conditional render)
22. Test banner logic (show/hide, localStorage)

**Phase 7: Polish & Testing**
23. Write component unit tests
24. Write integration tests
25. Manual QA on mobile viewport
26. Fix bugs and edge cases
27. Code review

**Phase 8: Documentation**
28. Update README with new feature
29. Add screenshots/GIFs if applicable
30. Document any configuration needed

## Technical Considerations

**Dependencies to Add:**
- `react-router-dom` (v6)

**Existing Dependencies to Use:**
- `@tanstack/react-query` (already installed)
- `axios` (via existing apiClient)
- `tailwindcss` (already configured)

**Browser Compatibility:**
- Modern browsers (Chrome, Safari, Firefox, Edge)
- Mobile browsers (iOS Safari, Chrome Mobile)
- localStorage support required (broadly supported)

**Performance:**
- React Query caching reduces API calls
- Optimistic updates improve perceived performance
- Lazy load images if channel avatars are large
- Debounce input if implementing search/autocomplete later

**Accessibility:**
- Semantic HTML (button, nav, header elements)
- ARIA labels for icon-only buttons
- Keyboard navigation support
- Focus management on modal/confirmation states
- Color contrast meets WCAG AA standards

**Security:**
- URLs validated server-side (backend already handles)
- No XSS risk (React escapes content by default)
- JWT token stored securely (existing pattern)
- HTTPS in production

## Success Criteria

**Functional Requirements:**
- ✅ Users can navigate to settings page
- ✅ Users can add YouTube channels via URL
- ✅ Users can add Instagram accounts via URL
- ✅ Users can delete channels with confirmation
- ✅ Users see personalized banner when no channels configured
- ✅ Banner dismissal persists across sessions
- ✅ API errors displayed clearly
- ✅ Loading states prevent double-submission

**Non-Functional Requirements:**
- ✅ Mobile-responsive (320px minimum width)
- ✅ Touch targets ≥ 44px
- ✅ Fast perceived performance (optimistic updates)
- ✅ Consistent with existing design language
- ✅ Accessible (keyboard navigation, screen readers)
- ✅ Unit test coverage ≥ 80%

**User Experience:**
- ✅ Simple, intuitive interface
- ✅ Clear error messages
- ✅ Immediate feedback on actions
- ✅ No unnecessary friction (optional onboarding)
- ✅ Easy to undo mistakes (delete confirmation)

## Future Enhancements (Out of Scope)

- Channel search/autocomplete
- Display channel metadata (subscriber count, description)
- Reorder channels (drag and drop)
- Bulk add channels (import from list)
- Channel tags/categories
- Recipe source analytics (which channels contribute most recipes)
- Sync channels across devices (requires backend change)
- Import channels from YouTube/Instagram API (requires OAuth)

## References

- Backend API: `/backend/app/routers/creators.py`
- Data Models: `/backend/app/models/recipe.py`
- Storage: `/backend/app/services/creator_store.py`
- Existing Frontend Patterns: `/frontend/src/pages/IngredientCollectionPage.tsx`
- Design System: Tailwind config and existing component styles

---

**Design Status:** ✅ Complete and Validated
**Ready for Implementation:** Yes
**Next Step:** Create git worktree and begin Phase 1 implementation
