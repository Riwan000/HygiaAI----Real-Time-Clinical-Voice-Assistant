# Deployment Guide

This document provides comprehensive instructions for deploying the HygiaAI frontend to production.

## Prerequisites

- Node.js v22.12+ or v20.19+ (required for Vite 7.2.2)
- npm or yarn package manager
- Vercel account (recommended) or another hosting platform
- Environment variables configured

## Environment Variables

Create a `.env.production` file or configure in your hosting platform:

```bash
# API Configuration
VITE_API_BASE_URL=https://api.hygiaai.com

# Feature Flags
VITE_ENABLE_OFFLINE_MODE=true
VITE_ENABLE_FEDERATED_LEARNING=true

# Analytics & Monitoring (Optional)
VITE_SENTRY_DSN=your_sentry_dsn_here
VITE_ANALYTICS_ID=your_analytics_id_here
VITE_ENABLE_ANALYTICS=true

# Environment
NODE_ENV=production
```

## Local Production Build

Test the production build locally before deploying:

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build:prod

# Preview production build
npm run preview:prod
```

The build output will be in the `dist/` directory.

## Vercel Deployment

### Option 1: Vercel CLI (Recommended)

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Login to Vercel:
```bash
vercel login
```

3. Deploy:
```bash
cd frontend
vercel
```

4. For production deployment:
```bash
vercel --prod
```

### Option 2: GitHub Integration

1. Connect your GitHub repository to Vercel
2. Configure environment variables in Vercel dashboard
3. Push to `main` branch triggers automatic production deployment
4. Pull requests create preview deployments

### Option 3: CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci.yml`) that:
- Runs linting and type checking
- Executes unit and E2E tests
- Builds production bundle
- Deploys to Vercel (preview for PRs, production for main branch)

**Required GitHub Secrets:**
- `VERCEL_TOKEN`: Vercel API token
- `VERCEL_ORG_ID`: Vercel organization ID
- `VERCEL_PROJECT_ID`: Vercel project ID
- `VITE_API_BASE_URL`: API base URL (optional, defaults to production)

## Build Optimization

The production build includes:

- **Code Splitting**: Automatic chunk splitting for optimal loading
- **Tree Shaking**: Unused code elimination
- **Minification**: JavaScript and CSS minification
- **Asset Optimization**: Image and font optimization
- **Source Maps**: Disabled in production for smaller bundles

### Bundle Analysis

Analyze bundle size:

```bash
npm run build:analyze
```

This generates a visual report of bundle composition.

## Performance Monitoring

### Web Vitals

The application automatically tracks Core Web Vitals:
- **LCP** (Largest Contentful Paint)
- **FID** (First Input Delay)
- **CLS** (Cumulative Layout Shift)
- **FCP** (First Contentful Paint)
- **TTFB** (Time to First Byte)
- **INP** (Interaction to Next Paint)

Metrics are logged in development and can be sent to analytics in production.

### Error Tracking

Sentry integration is available (optional):

1. Install Sentry:
```bash
npm install @sentry/react
```

2. Configure `VITE_SENTRY_DSN` environment variable

3. Errors are automatically captured and sent to Sentry

## Security Headers

Security headers are configured in `vercel.json`:
- Content Security Policy (CSP)
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy

## CORS Configuration

CORS is handled by the backend API. Ensure your API server includes:

```
Access-Control-Allow-Origin: https://your-frontend-domain.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

## Cache Strategy

Static assets are cached with long-term headers:
- JavaScript/CSS: `max-age=31536000, immutable`
- Images/Fonts: `max-age=31536000, immutable`
- HTML: No cache (always fetch fresh)

## Troubleshooting

### Build Fails

1. Check Node.js version: `node --version` (must be v22.12+ or v20.19+)
2. Clear cache: `rm -rf node_modules package-lock.json && npm install`
3. Check TypeScript errors: `npm run type-check`

### Deployment Fails

1. Verify environment variables are set correctly
2. Check build logs in Vercel dashboard
3. Ensure `vercel.json` is in the frontend directory
4. Verify API endpoints are accessible

### Performance Issues

1. Run bundle analysis: `npm run build:analyze`
2. Check Web Vitals in browser DevTools
3. Review network tab for large assets
4. Consider lazy loading for heavy components

## Rollback Procedure

### Vercel

1. Go to Vercel dashboard
2. Navigate to your project
3. Go to "Deployments" tab
4. Find previous successful deployment
5. Click "..." → "Promote to Production"

### Manual Rollback

1. Checkout previous commit:
```bash
git checkout <previous-commit-hash>
```

2. Rebuild and deploy:
```bash
npm run build:prod
vercel --prod
```

## Monitoring & Alerts

Set up monitoring for:
- Build failures (GitHub Actions notifications)
- Production errors (Sentry alerts)
- Performance degradation (Web Vitals monitoring)
- API availability (uptime monitoring)

## Support

For deployment issues:
1. Check build logs in CI/CD pipeline
2. Review Vercel deployment logs
3. Check browser console for runtime errors
4. Review Sentry for error tracking (if configured)

