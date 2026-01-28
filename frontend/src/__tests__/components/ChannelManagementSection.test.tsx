import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChannelManagementSection } from '../../components/ChannelManagementSection';
import { creatorsApi } from '../../api/creators';
import type { PreferredCreator } from '../../types';

vi.mock('../../api/creators', () => ({
  creatorsApi: {
    getCreators: vi.fn(),
    addCreator: vi.fn(),
    deleteCreator: vi.fn(),
  },
}));

const mockCreators: PreferredCreator[] = [
  {
    id: 'c1',
    user_id: 'user-1',
    source: 'youtube',
    creator_id: 'BabishCulinaryUniverse',
    creator_name: 'BabishCulinaryUniverse',
    added_at: '2026-01-27T00:00:00Z',
  },
];

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  );
}

describe('ChannelManagementSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty state when no creators exist', async () => {
    vi.mocked(creatorsApi.getCreators).mockResolvedValue([]);
    renderWithQuery(<ChannelManagementSection />);

    await waitFor(() => {
      expect(screen.getByText('No channels yet')).toBeInTheDocument();
    });
  });

  it('displays creators when they exist', async () => {
    vi.mocked(creatorsApi.getCreators).mockResolvedValue(mockCreators);
    renderWithQuery(<ChannelManagementSection />);

    await waitFor(() => {
      expect(screen.getByText('BabishCulinaryUniverse')).toBeInTheDocument();
    });
  });

  it('shows error for unrecognized URL', async () => {
    vi.mocked(creatorsApi.getCreators).mockResolvedValue([]);
    const user = userEvent.setup();
    renderWithQuery(<ChannelManagementSection />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Paste YouTube or Instagram URL')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Paste YouTube or Instagram URL');
    await user.type(input, 'https://www.tiktok.com/@someone');
    await user.click(screen.getByText('Add Channel'));

    expect(screen.getByText('Please enter a valid YouTube or Instagram URL.')).toBeInTheDocument();
  });

  it('adds creator on valid URL submission', async () => {
    vi.mocked(creatorsApi.getCreators).mockResolvedValue([]);
    vi.mocked(creatorsApi.addCreator).mockResolvedValue(mockCreators[0]);
    const user = userEvent.setup();
    renderWithQuery(<ChannelManagementSection />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Paste YouTube or Instagram URL')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Paste YouTube or Instagram URL');
    await user.type(input, 'https://www.youtube.com/@BabishCulinaryUniverse');
    await user.click(screen.getByText('Add Channel'));

    await waitFor(() => {
      expect(creatorsApi.addCreator).toHaveBeenCalled();
      const call = vi.mocked(creatorsApi.addCreator).mock.calls[0];
      expect(call[0]).toEqual({
        source: 'youtube',
        url: 'https://www.youtube.com/@BabishCulinaryUniverse',
      });
    });
  });
});
