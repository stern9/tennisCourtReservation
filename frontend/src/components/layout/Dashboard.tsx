// ABOUTME: Clean dashboard layout with header and full-width content
// ABOUTME: Mobile-friendly design without sidebar

'use client';

import { Header } from './Header';
import { cn } from '@/lib/utils';

interface DashboardProps {
  children: React.ReactNode;
  user?: {
    username: string;
    email: string;
  };
  onLogout?: () => void;
  className?: string;
}

const Dashboard = ({
  children,
  user,
  onLogout,
  className
}: DashboardProps) => {
  return (
    <div className={cn('min-h-screen bg-gray-50', className)}>
      {/* Header */}
      <Header
        user={user}
        onLogout={onLogout}
      />

      {/* Main Content */}
      <main className="p-4 sm:p-6 lg:p-8">
        {children}
      </main>
    </div>
  );
};

export { Dashboard };
export type { DashboardProps };