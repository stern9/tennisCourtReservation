// ABOUTME: Header component with user info and sign out functionality
// ABOUTME: Clean top navigation for better mobile experience

'use client';

import { Button } from '@/components/ui';
import { cn } from '@/lib/utils';

interface HeaderProps {
  user?: {
    username: string;
    email: string;
  };
  onLogout?: () => void;
  className?: string;
}

const Header = ({ 
  user,
  onLogout,
  className
}: HeaderProps) => {
  return (
    <header className={cn(
      'bg-white border-b border-gray-200 px-4 py-3',
      'flex items-center justify-between',
      className
    )}>
      {/* Logo/Title */}
      <div className="flex items-center space-x-2">
        <span className="text-lg font-bold text-gray-900">
          🎾 Tennis Court Booking
        </span>
      </div>

      {/* User Info & Sign Out */}
      {user && (
        <div className="flex items-center space-x-4">
          <div className="hidden sm:block text-right">
            <div className="text-sm font-medium text-gray-900">
              {user.username}
            </div>
            <div className="text-xs text-gray-500">
              {user.email}
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={onLogout}
          >
            Sign Out
          </Button>
        </div>
      )}
    </header>
  );
};

export { Header };
export type { HeaderProps };