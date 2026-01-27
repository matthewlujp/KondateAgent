import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { ChannelBanner } from '../../components/ChannelBanner';

describe('ChannelBanner', () => {

  it('renders banner content', () => {
    render(
      <MemoryRouter>
        <ChannelBanner onDismiss={vi.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText(/Add your favorite recipe channels/)).toBeInTheDocument();
  });

  it('has a link to settings', () => {
    render(
      <MemoryRouter>
        <ChannelBanner onDismiss={vi.fn()} />
      </MemoryRouter>
    );
    expect(screen.getByText('Add Channels')).toBeInTheDocument();
  });

  it('calls onDismiss when close button is clicked', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    render(
      <MemoryRouter>
        <ChannelBanner onDismiss={onDismiss} />
      </MemoryRouter>
    );

    await user.click(screen.getByLabelText('Dismiss'));
    expect(onDismiss).toHaveBeenCalled();
  });
});
