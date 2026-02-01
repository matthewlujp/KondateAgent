import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatFAB } from '../../src/components/ChatFAB';

describe('ChatFAB', () => {
  it('renders floating action button with chat icon', () => {
    const handleClick = vi.fn();
    render(<ChatFAB onClick={handleClick} />);

    const button = screen.getByRole('button', { name: /open chat/i });
    expect(button).toBeInTheDocument();
  });

  it('calls onClick when button is clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();
    render(<ChatFAB onClick={handleClick} />);

    const button = screen.getByRole('button', { name: /open chat/i });
    await user.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('hides button when isVisible is false', () => {
    const handleClick = vi.fn();
    render(<ChatFAB onClick={handleClick} isVisible={false} />);

    const button = screen.queryByRole('button', { name: /open chat/i });
    expect(button).not.toBeInTheDocument();
  });
});
