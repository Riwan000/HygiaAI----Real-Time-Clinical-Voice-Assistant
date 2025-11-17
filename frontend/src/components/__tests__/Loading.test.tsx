import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import { Loading, LoadingOverlay } from '../Loading';

describe('Loading', () => {
  it('renders loading spinner with default message', () => {
    render(<Loading />);
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('renders custom message', () => {
    render(<Loading message="Loading cases..." />);
    expect(screen.getByLabelText('Loading cases...')).toBeInTheDocument();
  });

  it('has aria-busy attribute', () => {
    render(<Loading />);
    const loading = screen.getByLabelText('Loading');
    expect(loading).toHaveAttribute('aria-busy', 'true');
  });
});

describe('LoadingOverlay', () => {
  it('renders overlay when loading', () => {
    render(
      <LoadingOverlay isLoading={true}>
        <div>Content</div>
      </LoadingOverlay>
    );
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('does not render overlay when not loading', () => {
    render(
      <LoadingOverlay isLoading={false}>
        <div>Content</div>
      </LoadingOverlay>
    );
    expect(screen.getByText('Content')).toBeInTheDocument();
    expect(screen.queryByLabelText('Loading')).not.toBeInTheDocument();
  });
});

