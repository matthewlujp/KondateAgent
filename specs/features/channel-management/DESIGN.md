---
inherits_from:
  - ../../../specs/ARCHITECTURE.md#api-design
  - ../../../specs/ARCHITECTURE.md#frontend-patterns
  - ../../../specs/DOMAIN.md#preferredcreator
status: implemented
---

# Design: Channel Management

Technical implementation of creator registration and management.

## Data Models

### PreferredCreator

```python
class PreferredCreator(BaseModel):
    id: str
    user_id: str
    source: Literal["youtube", "instagram"]
    creator_id: str      # Platform-specific ID
    creator_name: str    # Display name
    thumbnail_url: Optional[str]
    added_at: datetime
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/creators` | GET | List user's creators |
| `/api/creators` | POST | Add creator |
| `/api/creators/{id}` | DELETE | Remove creator |

### Add Creator Request/Response

```python
# Request
class AddCreatorRequest(BaseModel):
    url: str  # YouTube URL or Instagram handle

# Response
class CreatorResponse(BaseModel):
    creator: PreferredCreator
```

### List Response

```python
class CreatorsListResponse(BaseModel):
    creators: list[PreferredCreator]
```

## URL Parsing

### YouTube Formats

```python
def parse_youtube_url(url: str) -> Optional[str]:
    """Extract channel ID from various YouTube URL formats."""
    patterns = [
        r"youtube\.com/channel/(UC[\w-]+)",      # /channel/UCxxxxx
        r"youtube\.com/@([\w-]+)",               # /@handle
        r"youtube\.com/c/([\w-]+)",              # /c/ChannelName
    ]
    # Returns channel_id or None
```

### Instagram Formats

```python
def parse_instagram_url(url: str) -> Optional[str]:
    """Extract username from Instagram URL or handle."""
    patterns = [
        r"instagram\.com/([\w.]+)",              # instagram.com/username
        r"^@?([\w.]+)$",                         # @username or username
    ]
    # Returns username or None
```

## Backend Services

```python
class CreatorStore:
    _creators: dict[str, list[PreferredCreator]] = {}  # user_id → creators

    def list(self, user_id: str) -> list[PreferredCreator]: ...
    def add(self, user_id: str, creator: PreferredCreator) -> PreferredCreator: ...
    def remove(self, user_id: str, creator_id: str) -> bool: ...
    def get_by_source(self, user_id: str, source: str) -> list[PreferredCreator]: ...
```

### Validation

```python
class CreatorValidator:
    async def validate_youtube(self, channel_id: str) -> CreatorInfo:
        """Verify channel exists via YouTube API."""
        # Returns name, thumbnail, or raises error

    async def validate_instagram(self, username: str) -> CreatorInfo:
        """Basic format validation for Instagram."""
        # No API validation (third-party service limitations)
```

## Frontend Components

```
SettingsPage
└── ChannelManagementSection
    ├── AddChannelInput         # URL input with validation
    │   ├── Input field
    │   ├── Source detection badge
    │   └── Add button
    ├── ChannelCard[]           # List of creators
    │   ├── ChannelBanner       # Thumbnail, name
    │   ├── SourceBadge         # YouTube/Instagram icon
    │   └── DeleteButton
    └── EmptyState              # "No creators yet"
```

### AddChannelInput

```typescript
interface AddChannelInputProps {
  onAdd: (url: string) => Promise<void>;
  isLoading: boolean;
  error?: string;
}

// Auto-detects source from URL
// Shows YouTube/Instagram badge
// Validates before submit
```

### ChannelCard

```typescript
interface ChannelCardProps {
  creator: PreferredCreator;
  onDelete: (id: string) => void;
}

// Displays thumbnail, name, source badge
// Delete button with confirmation
```

## State Management

```typescript
// TanStack Query
const { data: creators } = useQuery({
  queryKey: ['creators', userId],
  queryFn: () => getCreators(userId),
});

const addMutation = useMutation({
  mutationFn: addCreator,
  onSuccess: () => queryClient.invalidateQueries(['creators']),
});

const deleteMutation = useMutation({
  mutationFn: deleteCreator,
  onSuccess: () => queryClient.invalidateQueries(['creators']),
});
```

## Error Handling

| Error | Detection | UI Response |
|-------|-----------|-------------|
| Invalid URL format | Regex mismatch | "Enter a valid YouTube or Instagram URL" |
| Channel not found | YouTube API 404 | "Channel not found on YouTube" |
| Already added | Duplicate check | "You've already added this creator" |
| Network error | Fetch failure | "Couldn't add creator. Try again?" |

## Integration with Recipe Search

Creators are used in `RecipeCollectionService`:

```python
async def search(self, user_id: str, ingredients: list[str]):
    creators = creator_store.list(user_id)
    youtube_channels = [c.creator_id for c in creators if c.source == "youtube"]
    instagram_accounts = [c.creator_id for c in creators if c.source == "instagram"]

    # Pass to search methods for priority boosting
    youtube_results = await self._search_youtube(queries, youtube_channels)
    instagram_results = await self._search_instagram(queries, instagram_accounts)
```

## Testing

### Unit Tests
- URL parsing: all supported formats
- Duplicate detection
- Store CRUD operations

### Integration Tests
- Add → list → delete flow
- YouTube API validation
- Creator priority in recipe search

### Frontend Tests
- AddChannelInput validation states
- ChannelCard rendering
- Empty state display

## Related Documents

- UI design: [Docs/plans/2026-01-27-channel-management-ui-design.md](../../../Docs/plans/2026-01-27-channel-management-ui-design.md)
- Backend: [Docs/plans/2026-01-27-recipe-source-configuration-design.md](../../../Docs/plans/2026-01-27-recipe-source-configuration-design.md)
