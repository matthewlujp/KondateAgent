import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CollapsibleSection } from '../../src/components/CollapsibleSection';

describe('CollapsibleSection', () => {
  it('renders with title and content expanded by default', () => {
    render(
      <CollapsibleSection title="Test Section">
        <div>Test Content</div>
      </CollapsibleSection>
    );

    expect(screen.getByText('Test Section')).toBeInTheDocument();
    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('collapses and expands when header is clicked', async () => {
    const user = userEvent.setup();
    render(
      <CollapsibleSection title="Test Section">
        <div>Test Content</div>
      </CollapsibleSection>
    );

    const header = screen.getByRole('button', { name: /test section/i });
    const content = screen.getByText('Test Content');

    expect(content).toBeVisible();

    await user.click(header);
    expect(content).not.toBeVisible();

    await user.click(header);
    expect(content).toBeVisible();
  });

  it('starts collapsed when defaultExpanded is false', () => {
    render(
      <CollapsibleSection title="Test Section" defaultExpanded={false}>
        <div>Test Content</div>
      </CollapsibleSection>
    );

    expect(screen.getByText('Test Content')).not.toBeVisible();
  });
});
