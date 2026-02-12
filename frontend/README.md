# TrueVow Financial Management - Frontend

React + TypeScript + Vite frontend application for the TrueVow Financial Management system.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router DOM** - Routing
- **React Query (TanStack Query)** - Data fetching and caching
- **React Hook Form** - Form handling
- **Zod** - Schema validation
- **Axios** - HTTP client

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn/pnpm

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The application will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The production build will be in the `dist` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── auth/            # Authentication components
│   │   ├── common/          # Common components (ErrorBoundary, LoadingSpinner, etc.)
│   │   └── layout/          # Layout components (Header, Sidebar, Layout)
│   ├── contexts/            # React contexts (Auth, Toast)
│   ├── hooks/               # Custom React hooks
│   ├── pages/               # Page components
│   │   ├── ar/              # Accounts Receivable pages
│   │   ├── ap/              # Accounts Payable pages
│   │   ├── auth/            # Authentication pages
│   │   ├── chart-of-accounts/
│   │   ├── dashboard/       # Dashboard page
│   │   ├── dimensions/
│   │   ├── journal-entries/
│   │   ├── payroll/          # Payroll pages
│   │   ├── periods/
│   │   ├── reports/         # Financial reports
│   │   └── treasury/        # Treasury pages
│   ├── services/            # API services
│   │   └── api/             # API client and endpoints
│   ├── utils/               # Utility functions
│   ├── App.tsx              # Main app component with routing
│   └── main.tsx             # Entry point
├── public/                   # Static assets
├── index.html               # HTML template
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Features

### Implemented Modules

1. **Authentication**
   - Login/logout
   - Protected routes
   - JWT token management

2. **General Ledger**
   - Journal entries (create, view, list)
   - Chart of Accounts (CRUD)
   - Accounting periods (create, close, lock)
   - Dimensions (CRUD)

3. **Accounts Receivable**
   - Invoice management
   - AR Aging reports
   - Deferred revenue schedules

4. **Accounts Payable**
   - Vendor management
   - Invoice entry
   - Payment processing
   - AP Aging reports

5. **Payroll**
   - Employee management
   - Payroll run workflow
   - Pay component management
   - Payment batch export (WPS, CSV)
   - Payslip viewer

6. **Treasury**
   - Bank account management
   - Transaction import (CSV)
   - Bank reconciliation
   - FX conversions
   - Inter-account transfers
   - Cash position dashboard

7. **Reporting**
   - Trial Balance
   - Profit & Loss
   - Balance Sheet
   - Cash Flow Statement
   - GL Detail viewer
   - Report export (PDF, Excel)

## Performance Optimizations

- **Code Splitting**: All pages are lazy-loaded for optimal bundle size
- **React Query**: Intelligent caching and data fetching
- **Skeleton Loaders**: Better perceived performance
- **Error Boundaries**: Graceful error handling

## Accessibility

- ARIA labels on interactive elements
- Keyboard navigation support
- Screen reader friendly
- WCAG 2.1 AA compliance target

## Environment Variables

Create a `.env` file in the `frontend` directory:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## API Integration

The frontend communicates with the FastAPI backend through REST APIs. All API calls are made through:

- `src/services/api/apiClient.ts` - Axios instance with interceptors
- `src/services/api/*Api.ts` - Module-specific API services

## Development Guidelines

1. **Component Structure**: Use functional components with hooks
2. **Type Safety**: Always type props and state
3. **Form Validation**: Use React Hook Form + Zod
4. **Error Handling**: Use error boundaries and toast notifications
5. **Loading States**: Always show loading indicators
6. **Responsive Design**: Mobile-first approach with Tailwind

## Testing

```bash
npm run test
```

## Linting

```bash
npm run lint
```

## License

Proprietary - TrueVow Financial Management System
