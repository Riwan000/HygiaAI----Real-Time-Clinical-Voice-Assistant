# HygiaAI Frontend

React + TypeScript frontend for HygiaAI Clinical Voice Assistant.

## Features

- Real-time medical transcription
- Clinical memory dashboard
- SOAP note generation and viewing
- Multimodal input (audio, text, images, lab reports)
- Outbreak and trend visualization
- Case timeline viewer
- Knowledge base browser
- Offline-first architecture
- WCAG 2.1 AA accessibility compliance

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **React Router** for navigation
- **Tailwind CSS** for styling
- **Plotly.js** for visualizations
- **Axios** for API calls
- **Headless UI** for accessible components

## Getting Started

### Prerequisites

- Node.js 20.19.0+ or 22.12.0+
- npm 11+

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `VITE_DEEPGRAM_API_KEY`: Deepgram API key for transcription
- `VITE_ENABLE_OFFLINE_MODE`: Enable offline functionality
- `VITE_ENABLE_FEDERATED_LEARNING`: Enable federated learning features

## Project Structure

```
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/          # Page components
│   ├── services/       # API services
│   ├── hooks/         # Custom React hooks
│   ├── utils/         # Utility functions
│   ├── types/         # TypeScript type definitions
│   └── main.tsx       # Entry point
├── public/            # Static assets
└── dist/              # Build output
```

## Code Quality

- ESLint for linting
- Prettier for code formatting
- TypeScript for type safety

Run linting:
```bash
npm run lint
```

Format code:
```bash
npm run format
```

## License

MIT

