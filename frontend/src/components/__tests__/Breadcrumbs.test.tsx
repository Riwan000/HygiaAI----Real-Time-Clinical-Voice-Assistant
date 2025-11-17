import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import { Breadcrumbs } from '../Breadcrumbs';

describe('Breadcrumbs', () => {
  it('renders breadcrumb items', () => {
    const items = [
      { name: 'Home', path: '/' },
      { name: 'Dashboard', path: '/dashboard' },
    ];
    render(<Breadcrumbs items={items} />);
    
    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
  });

  it('renders single item without separator', () => {
    const items = [{ name: 'Dashboard' }];
    render(<Breadcrumbs items={items} />);
    
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.queryByText('/')).not.toBeInTheDocument();
  });

  it('has proper navigation role', () => {
    const items = [{ name: 'Home' }];
    const { container } = render(<Breadcrumbs items={items} />);
    const nav = container.querySelector('nav');
    expect(nav).toHaveAttribute('aria-label', 'Breadcrumb');
  });
});

