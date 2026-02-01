import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChatBottomSheet } from '../../src/components/ChatBottomSheet';
import type { ChatMessage } from '../../src/types/mealPlan';

describe('ChatBottomSheet', () => {
  beforeEach(() => {
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();
  });
  const mockMessages: ChatMessage[] = [
    {
      role: 'user',
      content: 'Can you swap Tuesday?',
      timestamp: '2024-01-01T10:00:00Z',
    },
    {
      role: 'assistant',
      content: 'Sure! What would you prefer instead?',
      timestamp: '2024-01-01T10:00:05Z',
    },
  ];

  it('renders when isOpen is true', () => {
    const handleClose = vi.fn();
    const handleSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={true}
        onClose={handleClose}
        messages={mockMessages}
        onSendMessage={handleSendMessage}
        isLoading={false}
      />
    );

    // Should render backdrop
    expect(screen.getByTestId('chat-backdrop')).toBeInTheDocument();

    // Should render bottom sheet
    expect(screen.getByTestId('chat-bottom-sheet')).toBeInTheDocument();

    // Should render messages
    expect(screen.getByText('Can you swap Tuesday?')).toBeInTheDocument();
    expect(screen.getByText('Sure! What would you prefer instead?')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    const handleClose = vi.fn();
    const handleSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={false}
        onClose={handleClose}
        messages={[]}
        onSendMessage={handleSendMessage}
        isLoading={false}
      />
    );

    // Should not render backdrop or bottom sheet
    expect(screen.queryByTestId('chat-backdrop')).not.toBeInTheDocument();
    expect(screen.queryByTestId('chat-bottom-sheet')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    const handleSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={true}
        onClose={handleClose}
        messages={[]}
        onSendMessage={handleSendMessage}
        isLoading={false}
      />
    );

    const closeButton = screen.getByRole('button', { name: /close chat/i });
    await user.click(closeButton);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup();
    const handleClose = vi.fn();
    const handleSendMessage = vi.fn();

    render(
      <ChatBottomSheet
        isOpen={true}
        onClose={handleClose}
        messages={[]}
        onSendMessage={handleSendMessage}
        isLoading={false}
      />
    );

    const backdrop = screen.getByTestId('chat-backdrop');
    await user.click(backdrop);

    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
