# Testing Guide for HygiaAI Frontend

This document provides comprehensive information about the testing infrastructure and practices for the HygiaAI frontend application.

## Overview

The testing suite uses:
- **Vitest** - Fast unit test runner (Jest-compatible)
- **React Testing Library** - Component testing utilities
- **jest-axe** - Accessibility testing
- **MSW (Mock Service Worker)** - API mocking
- **Playwright** - End-to-end testing

## Test Structure

```
frontend/
├── src/
│   ├── test/
│   │   ├── setup.ts          # Global test configuration
│   │   ├── utils.tsx         # Custom render utilities
│   │   ├── mocks/
│   │   │   ├── handlers.ts   # MSW API handlers
│   │   │   └── server.ts     # MSW server setup
│   │   └── README.md         # Test documentation
│   ├── components/
│   │   └── __tests__/        # Component unit tests
│   └── services/
│       └── __tests__/         # Service integration tests
└── e2e/                       # End-to-end tests
    ├── dashboard.spec.ts
    ├── accessibility.spec.ts
    └── transcription.spec.ts
```

## Running Tests

### Unit Tests

```bash
# Run tests in watch mode (development)
npm run test

# Run tests with UI
npm run test:ui

# Run tests once (CI)
npm run test:run

# Run tests with coverage
npm run test:coverage
```

### E2E Tests

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

  it('handles user interactions', async () => {
    const user = userEvent.setup();
    render(<MyComponent />);
    
    const button = screen.getByRole('button');
    await user.click(button);
    
    expect(screen.getByText('Clicked')).toBeInTheDocument();
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
import { ClinicalMemoryService } from '../ClinicalMemoryService';

describe('ClinicalMemoryService', () => {
  it('calls API correctly', async () => {
    const result = await ClinicalMemoryService.recallSimilarCases({
      query_text: 'fever',
      limit: 5,
    });
    
    expect(result.success).toBe(true);
  });
});
```

## Mock Data

API requests are automatically mocked using MSW. Mock handlers are defined in `src/test/mocks/handlers.ts`.

### Customizing Mocks

```tsx
import { server } from '../../test/mocks/server';
import { http, HttpResponse } from 'msw';

it('handles API errors', async () => {
  server.use(
    http.get('/api/v1/clinical-memory/recall', () => {
      return HttpResponse.json(
        { success: false, error: 'Server error' },
        { status: 500 }
      );
    })
  );

  const result = await ClinicalMemoryService.recallSimilarCases({
    query_text: 'test',
    limit: 5,
  });

  expect(result.success).toBe(false);
});
```

## Best Practices

1. **Test user behavior, not implementation details**
   - Use `getByRole`, `getByLabelText` instead of `getByTestId`
   - Test what users see and interact with

2. **Use accessibility queries**
   - Prefer semantic queries (`getByRole`, `getByLabelText`)
   - These ensure components are accessible

3. **Test error states and edge cases**
   - Empty states
   - Loading states
   - Error messages
   - Network failures

4. **Keep tests isolated**
   - Each test should be independent
   - Use `beforeEach` for setup
   - Clean up after tests

5. **Use descriptive test names**
   - `it('should display error message when API fails')`
   - Not: `it('test 1')`

6. **Mock external dependencies**
   - Use MSW for API calls
   - Mock browser APIs (matchMedia, IntersectionObserver)

7. **Test accessibility**
   - Use `jest-axe` for automated accessibility testing
   - Test keyboard navigation
   - Test screen reader compatibility

## Common Patterns

### Testing Forms

```tsx
it('submits form with valid data', async () => {
  const user = userEvent.setup();
  const handleSubmit = vi.fn();
  
  render(<MyForm onSubmit={handleSubmit} />);
  
  await user.type(screen.getByLabelText('Name'), 'John');
  await user.click(screen.getByRole('button', { name: /submit/i }));
  
  expect(handleSubmit).toHaveBeenCalledWith({ name: 'John' });
});
```

### Testing Async Operations

```tsx
it('loads data on mount', async () => {
  render(<MyComponent />);
  
  expect(screen.getByText('Loading...')).toBeInTheDocument();
  
  await waitFor(() => {
    expect(screen.getByText('Data loaded')).toBeInTheDocument();
  });
});
```

### Testing Router Navigation

```tsx
it('navigates to correct page', async () => {
  const user = userEvent.setup();
  render(<MyComponent />);
  
  const link = screen.getByRole('link', { name: /dashboard/i });
  await user.click(link);
  
  expect(window.location.pathname).toBe('/dashboard');
});
```

## E2E Testing

E2E tests use Playwright and test full user workflows:

```typescript
test('user can search for cases', async ({ page }) => {
  await page.goto('/');
  
  const searchBox = page.getByRole('searchbox');
  await searchBox.fill('fever');
  await searchBox.press('Enter');
  
  await expect(page.locator('[data-testid="case-card"]').first()).toBeVisible();
});
```

## Continuous Integration

Tests run automatically on:
- Pull requests
- Commits to main branch
- Pre-commit hooks (optional)

## Troubleshooting

### Tests failing due to missing mocks

Ensure MSW server is set up in `setup.ts`:
```tsx
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Component not rendering

Check that providers are included in test utils:
```tsx
import { render } from '../../test/utils'; // Includes BrowserRouter
```

### Async operations timing out

Use `waitFor` or increase timeout:
```tsx
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument();
}, { timeout: 5000 });
```

## Resources

- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [jest-axe](https://github.com/nickcolley/jest-axe)
- [MSW Documentation](https://mswjs.io/)
- [Playwright Documentation](https://playwright.dev/)

