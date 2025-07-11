// ABOUTME: Reusable Button component with tennis court theme variants
// ABOUTME: Supports different sizes, styles, and states with proper accessibility

import { forwardRef, ButtonHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive' | 'court-green' | 'court-blue' | 'court-clay';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  loading?: boolean;
  fullWidth?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ 
    className, 
    variant = 'primary', 
    size = 'md', 
    loading = false,
    fullWidth = false,
    disabled,
    children, 
    ...props 
  }, ref) => {
    const baseStyles = [
      'inline-flex items-center justify-center rounded-md font-medium ring-offset-background transition-colors',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      'disabled:pointer-events-none disabled:opacity-50',
      'btn-bounce'
    ];

    const variantStyles = {
      primary: 'bg-accent-blue text-white hover:bg-blue-600 shadow-sm',
      secondary: 'bg-muted text-muted-foreground hover:bg-muted/80',
      outline: 'border border-border bg-background hover:bg-muted hover:text-muted-foreground',
      ghost: 'hover:bg-muted hover:text-muted-foreground',
      destructive: 'bg-red-500 text-white hover:bg-red-600 shadow-sm',
      'court-green': 'bg-court-green text-court-line hover:bg-green-700 shadow-sm',
      'court-blue': 'bg-court-blue text-court-line hover:bg-blue-700 shadow-sm',
      'court-clay': 'bg-court-clay text-court-line hover:bg-orange-700 shadow-sm',
    };

    const sizeStyles = {
      sm: 'h-8 px-3 text-sm',
      md: 'h-10 px-4 py-2',
      lg: 'h-12 px-8 text-lg',
      icon: 'h-10 w-10',
    };

    const widthStyles = fullWidth ? 'w-full' : '';

    return (
      <button
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          widthStyles,
          className
        )}
        disabled={disabled || loading}
        ref={ref}
        {...props}
      >
        {loading && (
          <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';

export { Button };
export type { ButtonProps };