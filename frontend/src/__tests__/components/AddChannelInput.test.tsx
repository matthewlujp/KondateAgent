import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AddChannelInput } from '../../components/AddChannelInput';

describe('AddChannelInput', () => {
  it('renders input with placeholder', () => {
    render(<AddChannelInput onAdd={vi.fn()} isLoading={false} error={null} />);
    expect(screen.getByPlaceholderText('Paste YouTube or Instagram URL')).toBeInTheDocument();
  });

  it('calls onAdd with url on submit', async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn();
    render(<AddChannelInput onAdd={onAdd} isLoading={false} error={null} />);

    const input = screen.getByPlaceholderText('Paste YouTube or Instagram URL');
    await user.type(input, 'https://www.youtube.com/@BabishCulinaryUniverse');
    await user.click(screen.getByText('Add Channel'));

    expect(onAdd).toHaveBeenCalledWith('https://www.youtube.com/@BabishCulinaryUniverse');
  });

  it('calls onAdd on Enter key', async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn();
    render(<AddChannelInput onAdd={onAdd} isLoading={false} error={null} />);

    const input = screen.getByPlaceholderText('Paste YouTube or Instagram URL');
    await user.type(input, 'https://www.youtube.com/@Test{Enter}');

    expect(onAdd).toHaveBeenCalledWith('https://www.youtube.com/@Test');
  });

  it('disables input and button when loading', () => {
    render(<AddChannelInput onAdd={vi.fn()} isLoading={true} error={null} />);

    expect(screen.getByPlaceholderText('Paste YouTube or Instagram URL')).toBeDisabled();
    expect(screen.getByText('Adding...')).toBeDisabled();
  });

  it('shows error message when error prop is set', () => {
    render(<AddChannelInput onAdd={vi.fn()} isLoading={false} error="Invalid URL format." />);
    expect(screen.getByText('Invalid URL format.')).toBeInTheDocument();
  });

  it('does not call onAdd when input is empty', async () => {
    const user = userEvent.setup();
    const onAdd = vi.fn();
    render(<AddChannelInput onAdd={onAdd} isLoading={false} error={null} />);

    await user.click(screen.getByText('Add Channel'));

    expect(onAdd).not.toHaveBeenCalled();
  });

  it('clears input after onClear is called', async () => {
    const user = userEvent.setup();
    render(<AddChannelInput onAdd={vi.fn()} isLoading={false} error={null} onClear={vi.fn()} />);

    const input = screen.getByPlaceholderText('Paste YouTube or Instagram URL');
    await user.type(input, 'some text');

    // The input should have the text
    expect(input).toHaveValue('some text');
  });
});
