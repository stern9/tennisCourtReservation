// ABOUTME: Minimal sidebar component for user info and logout
// ABOUTME: Clean design with just essential user information

'use client';

import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';

interface SidebarProps {
  user?: {
    username: string;
    email: string;
  };
  onLogout?: () => void;
  className?: string;
}

const Sidebar = ({ 
  user,
  onLogout,
  className
}: SidebarProps) => {
  return (
    <aside className={cn(
      'w-64 min-h-screen bg-gray-50 border-r border-gray-200 p-4',
      'flex flex-col',
      className
    )}>
      {/* User Info */}
      {user && (
        <div className="mb-6 p-4 bg-white rounded-lg border">
          <div className="text-sm font-medium text-gray-900">
            {user.username}
          </div>
          <div className="text-xs text-gray-500">
            {user.email}
          </div>
        </div>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Logout Button */}
      {onLogout && (
        <Button
          variant="outline"
          onClick={onLogout}
          fullWidth
          className="mt-auto"
        >
          Sign Out
        </Button>
      )}
    </aside>
  );
};

export { Sidebar };
export type { SidebarProps };