# SmartSPD v2 Frontend

Modern Next.js frontend for the SmartSPD AI-powered health plan assistant.

## 🚀 Quick Start

```bash
# From project root
./start_development.sh
```

## 🏗️ Architecture

### Tech Stack
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Auth0** - Enterprise authentication
- **React Query** - Server state management
- **Framer Motion** - Smooth animations
- **Lucide React** - Modern icon library

### Project Structure
```
frontend/
├── src/
│   ├── app/              # Next.js App Router pages
│   ├── components/       # Reusable components
│   │   ├── ui/          # Base UI components
│   │   ├── layout/      # Layout components
│   │   ├── chat/        # Chat interface
│   │   ├── admin/       # Admin dashboard
│   │   └── landing/     # Landing page
│   ├── lib/             # Utilities and API client
│   ├── hooks/           # Custom React hooks
│   ├── stores/          # State management
│   ├── types/           # TypeScript definitions
│   └── utils/           # Helper functions
├── public/              # Static assets
└── package.json         # Dependencies
```

## 🔧 Development Setup

### Prerequisites
- Node.js 18+
- npm or yarn
- Backend API running on port 8000

### Environment Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.local.example .env.local
   ```

3. Update `.env.local` with your Auth0 credentials:
   ```bash
   AUTH0_SECRET='your-secret-here'
   AUTH0_BASE_URL='http://localhost:3000'
   AUTH0_ISSUER_BASE_URL='https://your-domain.auth0.com'
   AUTH0_CLIENT_ID='your-client-id'
   AUTH0_CLIENT_SECRET='your-client-secret'
   AUTH0_AUDIENCE='https://api.smartspd.com'
   ```

### Run Development Server
```bash
npm run dev
```

The application will be available at http://localhost:3000