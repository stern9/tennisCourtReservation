// ABOUTME: Simple login form for tennis court booking authentication
// ABOUTME: Clean, minimal design with just username and password fields

'use client';

import { useState } from 'react';
import { Input, Button, Card, CardContent, CardHeader, CardTitle } from '@/components/ui';
import { validateRequired, cn } from '@/lib/utils';

interface LoginFormProps {
  onLogin: (credentials: { username: string; password: string }) => Promise<void>;
  loading?: boolean;
  error?: string;
  className?: string;
}

interface FormData {
  username: string;
  password: string;
}

interface FormErrors {
  username?: string;
  password?: string;
}

const LoginForm = ({ 
  onLogin, 
  loading = false, 
  error, 
  className 
}: LoginFormProps) => {
  const [formData, setFormData] = useState<FormData>({
    username: '',
    password: '',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!validateRequired(formData.username)) {
      newErrors.username = 'Username is required';
    }

    if (!validateRequired(formData.password)) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    
    try {
      await onLogin(formData);
    } catch (err) {
      // Error handling is done by parent component
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof FormData) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const value = e.target.value;
    
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <Card className={cn('w-full max-w-md mx-auto', className)}>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">
          🎾 Tennis Court Booking
        </CardTitle>
        <p className="text-muted-foreground">
          Sign in to manage your reservations
        </p>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          )}

          <Input
            label="Username"
            type="text"
            value={formData.username}
            onChange={handleInputChange('username')}
            error={errors.username}
            placeholder="Enter your username"
            required
            fullWidth
          />

          <Input
            label="Password"
            type="password"
            value={formData.password}
            onChange={handleInputChange('password')}
            error={errors.password}
            placeholder="Enter your password"
            required
            fullWidth
          />

          <Button
            type="submit"
            variant="court-green"
            size="lg"
            fullWidth
            loading={isSubmitting || loading}
            disabled={isSubmitting || loading}
          >
            {isSubmitting || loading ? 'Signing in...' : 'Sign In'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export { LoginForm };
export type { LoginFormProps };