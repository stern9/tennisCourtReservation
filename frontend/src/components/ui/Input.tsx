// ABOUTME: Reusable Input component with validation and tennis court theme
// ABOUTME: Supports different types, states, and custom validation messages

import { forwardRef, InputHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  fullWidth?: boolean;
  variant?: 'default' | 'court';
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    className, 
    type = 'text',
    label,
    error,
    helperText,
    fullWidth = false,
    variant = 'default',
    id,
    ...props 
  }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    const baseStyles = [
      'flex h-10 w-full rounded-md border border-border bg-input px-3 py-2 text-sm ring-offset-background',
      'file:border-0 file:bg-transparent file:text-sm file:font-medium',
      'placeholder:text-muted-foreground',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      'disabled:cursor-not-allowed disabled:opacity-50',
      'transition-colors fade-in'
    ];

    const variantStyles = {
      default: '',
      court: 'border-court-green focus-visible:ring-court-green',
    };

    const errorStyles = error 
      ? 'border-red-500 focus-visible:ring-red-500' 
      : '';

    const widthStyles = fullWidth ? 'w-full' : '';

    return (
      <div className={cn('space-y-1', fullWidth && 'w-full')}>
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-sm font-medium text-foreground"
          >
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <input
          type={type}
          id={inputId}
          className={cn(
            baseStyles,
            variantStyles[variant],
            errorStyles,
            widthStyles,
            className
          )}
          ref={ref}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-500 mt-1 flex items-center">
            <span className="mr-1">⚠️</span>
            {error}
          </p>
        )}
        {helperText && !error && (
          <p className="text-sm text-muted-foreground mt-1">
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export { Input };
export type { InputProps };