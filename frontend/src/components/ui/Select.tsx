// ABOUTME: Reusable Select component for dropdown menus with tennis court theme
// ABOUTME: Supports validation, custom options, and consistent styling

import { forwardRef, SelectHTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
  placeholder?: string;
  fullWidth?: boolean;
  variant?: 'default' | 'court';
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ 
    className, 
    label,
    error,
    helperText,
    options,
    placeholder,
    fullWidth = false,
    variant = 'default',
    id,
    ...props 
  }, ref) => {
    const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    const baseStyles = [
      'flex h-10 w-full rounded-md border border-border bg-input px-3 py-2 text-sm ring-offset-background',
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
            htmlFor={selectId}
            className="block text-sm font-medium text-foreground"
          >
            {label}
            {props.required && <span className="text-red-500 ml-1">*</span>}
          </label>
        )}
        <select
          id={selectId}
          className={cn(
            baseStyles,
            variantStyles[variant],
            errorStyles,
            widthStyles,
            className
          )}
          ref={ref}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option 
              key={option.value} 
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
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

Select.displayName = 'Select';

export { Select };
export type { SelectProps, SelectOption };