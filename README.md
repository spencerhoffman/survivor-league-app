# Survivor League - Next.js Application

A complete migration of the Survivor League application from React + Vite frontend with FastAPI backend to a full Next.js application with API routes for Vercel deployment.

## Overview

This is a **Survivor League** web application that enables users to participate in a weekly elimination-style fantasy sports game. Users create player entries and make weekly team picks, with the goal of surviving as long as possible without their selected teams losing.

## Migration Details

### Original Architecture
- **Backend**: FastAPI (Python) with single-file architecture (`main.py`)
- **Frontend**: React + Vite with single-component architecture (`App.tsx`)
- **Database**: In-memory storage with PostgreSQL configuration
- **UI**: shadcn/ui components with Tailwind CSS

### New Architecture
- **Full-Stack**: Next.js 15 with App Router
- **API Routes**: 25+ endpoints migrated from FastAPI to Next.js API routes
- **Database**: Vercel Postgres with proper schema
- **Authentication**: JWT-based with Next.js middleware
- **UI**: Preserved shadcn/ui components and Tailwind CSS
- **State Management**: React hooks (as requested)
- **File Uploads**: Included directly in git repository (as requested)

## Key Features

- **User Authentication**: JWT-based login/register with role-based access
- **Player Management**: Create multiple entries per user account
- **Weekly Picks**: Submit team selections with validation and locking
- **Elimination System**: Automatic player elimination based on game results
- **Redemption Rounds**: Second chance system with underdog team requirements
- **Buyback System**: Pay to re-enter after elimination
- **Admin Panel**: Complete game management interface
- **Leaderboard**: Track survival progress and rankings

## Technology Stack

- **Framework**: Next.js 15 with App Router
- **Database**: Vercel Postgres
- **Authentication**: JWT with bcryptjs
- **UI Components**: shadcn/ui + Radix UI
- **Styling**: Tailwind CSS
- **TypeScript**: Full type safety
- **Deployment**: Optimized for Vercel

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration with profile picture
- `POST /api/auth/login` - JWT authentication
- `POST /api/auth/reset-password` - Password reset

### Player Management
- `POST /api/players` - Create player entries
- `GET /api/players/me` - Get user's players
- `POST /api/players/[id]/picks` - Submit weekly picks
- `GET /api/players/[id]/picks` - Get player's picks
- `PUT /api/players/[id]/picks/[pickId]` - Update pick
- `DELETE /api/players/[id]/picks/[pickId]` - Delete pick
- `POST /api/players/[id]/redemption-picks` - Submit redemption picks
- `POST /api/players/[id]/buyback` - Process buyback

### Admin Routes
- `POST /api/admin/advance-week` - Progress to next week
- `POST /api/admin/lock-picks` - Lock pick submissions
- `POST /api/admin/unlock-picks` - Unlock pick submissions
- `POST /api/admin/process-week-results` - Process eliminations
- `POST /api/admin/record-result` - Record game outcomes
- `GET /api/admin/settings` - Get game settings

### General
- `GET /api/me` - Get current user info
- `GET /api/teams` - Get available teams
- `GET /api/leaderboard` - Get player standings
- `GET /api/healthz` - Health check

## Database Schema

The application uses Vercel Postgres with the following tables:
- `users` - User accounts and authentication
- `players` - Game entries (multiple per user)
- `weekly_picks` - Team selections by week
- `game_results` - Game outcomes for elimination processing
- `underdog_teams` - Designated underdog teams for redemption
- `game_settings` - Global game configuration

## Environment Variables

```bash
# Database
DATABASE_URL=your_vercel_postgres_url

# Authentication
JWT_SECRET_KEY=your_jwt_secret

# Admin
ADMIN_PASSWORD=your_admin_password
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Deployment

This application is optimized for Vercel deployment:

1. Connect your repository to Vercel
2. Set up Vercel Postgres database
3. Configure environment variables
4. Deploy automatically on push

## Migration Verification

All original functionality has been preserved:
- ✅ User authentication and authorization
- ✅ Player entry creation and management
- ✅ Weekly pick submission and validation
- ✅ Elimination and redemption logic
- ✅ Buyback calculations
- ✅ Admin game management
- ✅ Leaderboard and standings
- ✅ File upload handling
- ✅ shadcn/ui component library
- ✅ Responsive design with Tailwind CSS

## Business Logic Preservation

Critical game mechanics maintained:
- Player elimination based on losing team picks
- Redemption round system with 3-pick requirement
- Underdog team validation for redemption
- Buyback cost calculation (week × multiplier)
- Week advancement and pick locking
- Financial contribution tracking

## Link to Devin Run
https://app.devin.ai/sessions/be4171c9a7d94a6aada0aff34cac083c

## Requested by
@spencerhoffman
