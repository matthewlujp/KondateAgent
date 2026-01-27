import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChannelCard } from '../../components/ChannelCard';
import type { PreferredCreator } from '../../types';

const youtubeCreator: PreferredCreator = {
  id: 'creator-1',
  user_id: 'user-1',
  source: 'youtube',
  creator_id: 'BabishCulinaryUniverse',
  creator_name: 'BabishCulinaryUniverse',
  added_at: '2026-01-27T00:00:00Z',
};

const instagramCreator: PreferredCreator = {
  id: 'creator-2',
  user_id: 'user-1',
  source: 'instagram',
  creator_id: 'foodblogger',
  creator_name: 'foodblogger',
  added_at: '2026-01-27T00:00:00Z',
};

describe('ChannelCard', () => {
  it('renders channel name', () => {
    render(<ChannelCard channel={youtubeCreator} onDelete={vi.fn()} />);
    expect(screen.getByText('BabishCulinaryUniverse')).toBeInTheDocument();
  });

  it('shows YouTube badge for youtube source', () => {
    render(<ChannelCard channel={youtubeCreator} onDelete={vi.fn()} />);
    expect(screen.getByText('YouTube')).toBeInTheDocument();
  });

  it('shows Instagram badge for instagram source', () => {
    render(<ChannelCard channel={instagramCreator} onDelete={vi.fn()} />);
    expect(screen.getByText('Instagram')).toBeInTheDocument();
  });

  it('shows delete confirmation on delete click', async () => {
    const user = userEvent.setup();
    render(<ChannelCard channel={youtubeCreator} onDelete={vi.fn()} />);

    await user.click(screen.getByLabelText('Delete channel'));
    expect(screen.getByText(/Remove BabishCulinaryUniverse\?/)).toBeInTheDocument();
  });

  it('calls onDelete when confirmation is confirmed', async () => {
    const user = userEvent.setup();
    const onDelete = vi.fn();
    render(<ChannelCard channel={youtubeCreator} onDelete={onDelete} />);

    await user.click(screen.getByLabelText('Delete channel'));
    await user.click(screen.getByText('Remove'));

    expect(onDelete).toHaveBeenCalledWith('creator-1');
  });

  it('hides confirmation when Cancel is clicked', async () => {
    const user = userEvent.setup();
    render(<ChannelCard channel={youtubeCreator} onDelete={vi.fn()} />);

    await user.click(screen.getByLabelText('Delete channel'));
    await user.click(screen.getByText('Cancel'));

    expect(screen.queryByText(/Remove BabishCulinaryUniverse\?/)).not.toBeInTheDocument();
  });
});
