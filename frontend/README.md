# Tennis Court Reservation - Frontend

This is the frontend application for the Tennis Court Reservation System, built with Next.js 15, TypeScript, and Tailwind CSS.

## Features

- **Modern UI/UX**: Clean, responsive design with tennis court theming
- **Real-time Updates**: Live court status and booking updates
- **State Management**: Zustand for efficient state management
- **API Integration**: Seamless connection to FastAPI backend
- **Type Safety**: Full TypeScript support throughout
- **Responsive Design**: Works on desktop, tablet, and mobile

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS with custom tennis court theme
- **State Management**: Zustand with persistence
- **HTTP Client**: Axios with interceptors
- **Development**: ESLint, Prettier, Husky

## Getting Started

### Prerequisites

- Node.js 18.18.0 or higher
- npm 9.0.0 or higher

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

### Environment Variables

Create a `.env.local` file with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── globals.css         # Global styles and theme
│   │   ├── layout.tsx          # Root layout
│   │   └── page.tsx            # Home page
│   ├── components/             # React components
│   │   ├── ui/                 # Base UI components
│   │   ├── forms/              # Form components
│   │   └── layout/             # Layout components
│   ├── hooks/                  # Custom React hooks
│   │   └── useApi.ts           # API integration hooks
│   ├── lib/                    # Utilities and configurations
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Utility functions
│   ├── store/                  # State management
│   │   └── index.ts            # Zustand store
│   └── styles/                 # Additional styles
├── public/                     # Static assets
└── package.json                # Dependencies and scripts
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript checks

## Features Implementation

### Phase 3.1: ✅ Frontend Project Setup
- Next.js 15 project initialization
- TypeScript configuration
- Tailwind CSS with tennis court theme
- Zustand state management
- Axios API client
- Project structure organization

### Phase 3.2: 🔄 Basic Configuration Form
- User configuration interface
- Form validation and submission
- API integration for config management

### Phase 3.3: 📋 User Interface Enhancement
- Court status visualization
- Booking management interface
- Real-time status updates
- Tennis automation controls

### Phase 3.4: 🔄 Real-time Updates
- WebSocket integration
- Live court availability
- Booking status notifications
- Automated refresh mechanisms

## API Integration

The frontend communicates with the FastAPI backend through a comprehensive API client:

- **Configuration**: Save/load user settings
- **Bookings**: Create, update, and manage reservations
- **Court Status**: Real-time availability checking
- **Automation**: Control tennis booking automation
- **Health Checks**: Monitor backend connectivity

## State Management

Uses Zustand for efficient state management with:

- **Persistence**: Automatic localStorage sync
- **Type Safety**: Full TypeScript support
- **Selectors**: Optimized state access
- **Actions**: Centralized state mutations

## Styling

Custom tennis court theme with:

- **Court Colors**: Green, blue, clay surface colors
- **Status Indicators**: Available, occupied, pending states
- **Responsive Design**: Mobile-first approach
- **Dark Mode**: Automatic theme switching
- **Animations**: Smooth transitions and interactions

## Development

### Code Style

- **ESLint**: Airbnb configuration
- **Prettier**: Code formatting
- **Husky**: Pre-commit hooks
- **TypeScript**: Strict mode enabled

### Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run e2e tests
npm run test:e2e
```

## Deployment

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Environment Configuration

Configure environment variables for different deployment targets:

- **Development**: `.env.local`
- **Production**: `.env.production`
- **Docker**: Environment variables in container

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Submit PR with clear description

## License

This project is part of the Tennis Court Reservation System and follows the same license terms.