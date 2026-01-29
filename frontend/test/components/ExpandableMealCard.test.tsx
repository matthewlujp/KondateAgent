import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ExpandableMealCard } from '../../src/components/ExpandableMealCard';
import type { MealSlot, Recipe } from '../../src/types';

describe('ExpandableMealCard', () => {
  const mockSlot: MealSlot = {
    id: 'slot-1',
    day: 'monday',
    enabled: true,
    recipe_id: 'recipe-1',
    swap_count: 0,
  };

  const mockRecipe: Recipe = {
    id: 'recipe-1',
    source: 'youtube',
    source_id: 'yt123',
    url: 'https://youtube.com/watch?v=test',
    thumbnail_url: 'https://example.com/thumb.jpg',
    title: 'Delicious Pasta',
    creator_name: 'Chef John',
    creator_id: 'chef123',
    extracted_ingredients: ['pasta', 'tomatoes', 'garlic', 'olive oil', 'basil'],
    raw_description: 'A simple and delicious pasta recipe with fresh ingredients',
    duration: 1800, // 30 minutes in seconds
    posted_at: '2024-01-15T10:00:00Z',
    cache_expires_at: '2024-01-16T10:000Z',
  };

  it('renders disabled state for skipped day', () => {
    const disabledSlot = { ...mockSlot, enabled: false };
    render(<ExpandableMealCard slot={disabledSlot} />);

    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('Skipped')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders empty state when no recipe assigned', () => {
    const emptySlot = { ...mockSlot, recipe_id: undefined };
    render(<ExpandableMealCard slot={emptySlot} />);

    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('No recipe assigned')).toBeInTheDocument();
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });

  it('renders collapsed state with recipe and expands on click', async () => {
    const user = userEvent.setup();
    render(<ExpandableMealCard slot={mockSlot} recipe={mockRecipe} />);

    // Collapsed state - should show basic info
    expect(screen.getByText('Monday')).toBeInTheDocument();
    expect(screen.getByText('Delicious Pasta')).toBeInTheDocument();
    expect(screen.getByText('Chef John')).toBeInTheDocument();
    expect(screen.getByAltText('Delicious Pasta')).toHaveAttribute(
      'src',
      'https://example.com/thumb.jpg'
    );

    // Should have expand button
    const expandButton = screen.getByRole('button', { name: /expand/i });
    expect(expandButton).toBeInTheDocument();

    // Should NOT show expanded content initially
    expect(screen.queryByText('30 min')).not.toBeInTheDocument();
    expect(screen.queryByText(/A simple and delicious pasta recipe/)).not.toBeInTheDocument();

    // Click to expand
    await user.click(expandButton);

    // Should show expanded content
    expect(screen.getByText('30 min')).toBeInTheDocument();
    expect(screen.getByText(/A simple and delicious pasta recipe/)).toBeInTheDocument();
    expect(screen.getByText('pasta')).toBeInTheDocument();
    expect(screen.getByText('tomatoes')).toBeInTheDocument();
    expect(screen.getByText('garlic')).toBeInTheDocument();
    expect(screen.getByText('olive oil')).toBeInTheDocument();
    expect(screen.getByText('basil')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /view recipe/i })).toHaveAttribute(
      'href',
      'https://youtube.com/watch?v=test'
    );

    // Click to collapse
    const collapseButton = screen.getByRole('button', { name: /collapse/i });
    await user.click(collapseButton);

    // Should hide expanded content again
    expect(screen.queryByText('30 min')).not.toBeInTheDocument();
    expect(screen.queryByText(/A simple and delicious pasta recipe/)).not.toBeInTheDocument();
  });

  it('handles recipe without duration', async () => {
    const user = userEvent.setup();
    const recipeNoDuration = { ...mockRecipe, duration: undefined };
    render(<ExpandableMealCard slot={mockSlot} recipe={recipeNoDuration} />);

    const expandButton = screen.getByRole('button', { name: /expand/i });
    await user.click(expandButton);

    // Should not show duration when not available
    expect(screen.queryByText(/min/)).not.toBeInTheDocument();
  });
});
