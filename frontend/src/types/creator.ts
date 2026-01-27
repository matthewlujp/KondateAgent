export type CreatorSource = 'youtube' | 'instagram';

export interface PreferredCreator {
  id: string;
  user_id: string;
  source: CreatorSource;
  creator_id: string;
  creator_name: string;
  added_at: string;
}

export interface AddCreatorRequest {
  source: CreatorSource;
  url: string;
}
