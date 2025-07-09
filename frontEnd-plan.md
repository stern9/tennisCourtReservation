# Frontend Implementation Plan: Tennis Court Booking System

This document outlines the steps for an LLM to build the frontend for the Tennis Court Booking System. The stack is Next.js, TypeScript, shadcn/ui, Tailwind CSS, TanStack Query, React Hook Form, and Zustand.

## Phase 1: Project Initialization & Scaffolding

**Objective:** Set up a new Next.js project with all required dependencies and a clean directory structure.

### Step 1.1: Create Next.js Application
- Use `create-next-app` to initialize the project.
- **Command:**
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
  ```
- Navigate into the new directory: `cd frontend`

### Step 1.2: Initialize shadcn/ui
- Initialize shadcn/ui, which will set up `components.json` and global styles.
- **Command:**
  ```bash
  npx shadcn-ui@latest init
  ```
- **Selections:**
  - Style: **Default**
  - Base color: **Slate**
  - CSS variables: **Yes**

### Step 1.3: Install Core Dependencies
- Install all necessary libraries for state management, data fetching, forms, and utilities.
- **Command:**
  ```bash
  npm install axios react-hook-form @hookform/resolvers zod zustand @tanstack/react-query lucide-react clsx tailwind-merge
  ```

### Step 1.4: Set Up Project Structure
- Create the standard directories for organizing the codebase.
- **Command:**
  ```bash
  mkdir -p src/lib src/hooks src/store src/app/api
  ```
- **Structure:**
  - `src/app/`: Page routes and layouts.
  - `src/app/api/`: Next.js API routes (for proxying/auth).
  - `src/components/`: Reusable UI components (shadcn and custom).
  - `src/lib/`: Helper functions, API client, utils.
  - `src/hooks/`: Custom React hooks.
  - `src/store/`: Zustand state management stores.

### Step 1.5: Configure Environment Variables
- Create a file for environment variables.
- **File:** `.env.local`
- **Content:**
  ```
  NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api
  ```

## Phase 2: API Client, Auth, and Core Layout

**Objective:** Establish the API communication layer, set up authentication flow, and create the main application layout with protected routing.

### Step 2.1: Create API Client
- Create a configured Axios instance for making API calls.
- **File:** `src/lib/api.ts`
- **Action:** Implement a function that creates an Axios instance. It should be able to dynamically add the Authorization header.

### Step 2.2: Create Auth Store
- Create a Zustand store to manage the user's authentication state globally.
- **File:** `src/store/authStore.ts`
- **Action:** The store should hold the user object and authentication status.

### Step 2.3: Implement Auth Route Handler
- Create a Next.js API route to handle login. This route will call the backend, and on success, it will set a secure, `httpOnly` cookie containing the JWT.
- **File:** `src/app/api/auth/login/route.ts`
- **Action:**
  - Accept POST requests with user credentials.
  - Call the FastAPI backend's `/auth/token` endpoint.
  - On success, get the JWT and set it in an `httpOnly` cookie.
  - Return a success response.

### Step 2.4: Create Login Page
- Build the UI for the login page.
- **File:** `src/app/login/page.tsx`
- **Action:**
  - Use shadcn/ui `Card`, `Input`, `Button`, and `Label` components.
  - Use `React Hook Form` and `Zod` for form state and validation.
  - On submit, call the `/api/auth/login` route handler created in the previous step.
  - On success, redirect the user to the dashboard.
  - Add a `Toaster` component to show error messages.

### Step 2.5: Implement Middleware for Protected Routes
- Create middleware to protect application routes from unauthenticated access.
- **File:** `src/middleware.ts`
- **Action:**
  - Check for the auth cookie.
  - If the cookie is missing and the user is trying to access a protected route (e.g., `/dashboard`), redirect them to `/login`.
  - Define which routes are public (`/login`) and which are protected.

### Step 2.6: Create Core Layout and Header
- Create a persistent layout with a header that displays navigation and user status.
- **File:** `src/app/layout.tsx`
- **Action:** Add the `Toaster` from shadcn/ui here.
- **File:** `src/components/layout/Header.tsx`
- **Action:**
  - Display navigation links.
  - Conditionally show "Login" or "Logout" and user info based on the auth state from the Zustand store.
  - The "Logout" button should call an API route (`/api/auth/logout`) that clears the auth cookie.

## Phase 3: Feature Implementation

**Objective:** Build the core features of the application: booking form and booking history dashboard.

### Step 3.1: Create TanStack Query Provider
- Wrap the application in a QueryClientProvider to enable TanStack Query.
- **File:** `src/components/providers/QueryProvider.tsx`
- **Action:** Create a client component that initializes `QueryClient` and provides it to its children.
- **File:** `src/app/layout.tsx`
- **Action:** Wrap the main content in the `QueryProvider`.

### Step 3.2: Create Booking Form
- Build the page for creating a new booking request.
- **File:** `src/app/book/page.tsx`
- **Action:**
  - This is a protected route.
  - Use shadcn/ui components: `Input`, `DatePicker`, `Select`, `Button`.
  - Use `React Hook Form` and `Zod` for validation (date, time slot, court preference).
  - Use TanStack Query's `useMutation` hook to submit the form data to the backend's `/bookings` endpoint.
  - On success, show a toast notification and redirect to the dashboard.

### Step 3.3: Create Dashboard Page
- Build the page to display a user's past and upcoming bookings.
- **File:** `src/app/dashboard/page.tsx`
- **Action:**
  - This is a protected route.
  - Use TanStack Query's `useQuery` hook to fetch data from the `/bookings` endpoint.
  - Display the bookings in a `Table` component from shadcn/ui.
  - For each booking, display the status (`PENDING`, `CONFIRMED`, `FAILED`).

### Step 3.4: Implement Real-Time Status Polling
- Enhance the dashboard to automatically update booking statuses.
- **File:** `src/app/dashboard/page.tsx`
- **Action:**
  - In the `useQuery` hook that fetches bookings, set a `refetchInterval`.
  - Set the interval to a reasonable value (e.g., 5000ms) for bookings with a `PENDING` status.
  - The UI will automatically update when the data is re-fetched and the status has changed.

## Phase 4: Finalization

**Objective:** Polish the application, add final touches, and ensure it's ready for use.

### Step 4.1: Add shadcn/ui Components
- Throughout the process, add all required shadcn/ui components as needed.
- **Command (example):**
  ```bash
  npx shadcn-ui@latest add button card input label select table date-picker toast toaster
  ```

### Step 4.2: Responsive Design
- Review all pages and ensure they are fully responsive on mobile and tablet devices using Tailwind CSS utility classes.

### Step 4.3: Custom Not Found Page
- Create a custom 404 page to improve user experience.
- **File:** `src/app/not-found.tsx`

### Step 4.4: Update README
- Create a comprehensive `README.md` in the `frontend` directory.
- **Action:** Include instructions on how to install dependencies (`npm install`) and how to run the development server (`npm run dev`).
