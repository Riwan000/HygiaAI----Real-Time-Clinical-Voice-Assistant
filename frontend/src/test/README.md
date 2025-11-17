# Testing Guide

This directory contains the test suite for the HygiaAI frontend application.

## Test Structure

- `setup.ts` - Test configuration and global setup
- `utils.tsx` - Custom render utilities with providers
- `mocks/` - MSW handlers for API mocking
- `__tests__/` - Component and service unit tests
- `e2e/` - End-to-end tests with Playwright

## Running Tests

### Unit Tests (Vitest)

```bash
# Run tests in watch mode
npm run test

# Run tests with UI
npm run test:ui

# Run tests once
npm run test:run

# Run tests with coverage
npm run test:coverage
```

### E2E Tests (Playwright)

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui
```

## Test Coverage Goals

- **Lines**: 80%+
- **Functions**: 80%+
- **Branches**: 80%+
- **Statements**: 80%+

## Writing Tests

### Component Tests

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/utils';
import { MyComponent } from '../MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### Accessibility Tests

```tsx
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Service Tests

```tsx
import { describe, it, expect } from 'vitest';
import { MyService } from '../MyService';

describe('MyService', () => {
  it('calls API correctly', async () => {
    const result = await MyService.getData();
    expect(result.success).toBe(true);
  });
});
```

## Mock Data

API requests are automatically mocked using MSW (Mock Service Worker). See `mocks/handlers.ts` for mock implementations.

## Best Practices

1. **Test user behavior, not implementation details**
2. **Use accessibility queries** (`getByRole`, `getByLabelText`)
3. **Test error states and edge cases**
4. **Keep tests isolated and independent**
5. **Use descriptive test names**
6. **Mock external dependencies**
7. **Test accessibility with jest-axe**

