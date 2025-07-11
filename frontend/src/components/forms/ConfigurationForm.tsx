// ABOUTME: Configuration form for tennis court booking preferences and settings
// ABOUTME: Allows users to set their booking preferences, credentials, and court options

'use client';

import { useState, useEffect } from 'react';
import { Input, Button, Card, CardContent, CardHeader, CardTitle, Select } from '@/components/ui';
import { validateRequired, validateEmail, cn } from '@/lib/utils';
import { TennisConfig } from '@/store';

interface ConfigurationFormProps {
  initialConfig?: TennisConfig | null;
  onSave: (config: TennisConfig) => Promise<void>;
  loading?: boolean;
  error?: string;
  className?: string;
}

interface FormErrors {
  [key: string]: string | undefined;
}

const ConfigurationForm = ({ 
  initialConfig, 
  onSave, 
  loading = false, 
  error, 
  className 
}: ConfigurationFormProps) => {
  const [formData, setFormData] = useState<TennisConfig>({
    club_name: '',
    location: '',
    username: '',
    password: '',
    preferred_times: [],
    court_preferences: [],
    booking_advance_days: 7,
    auto_book: false,
    notification_email: '',
    court_surface: 'hard',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Load initial config
  useEffect(() => {
    if (initialConfig) {
      setFormData(initialConfig);
    }
  }, [initialConfig]);

  const timeSlotOptions = [
    { value: 'De 08:00 AM a 09:00 AM', label: '8:00 AM - 9:00 AM' },
    { value: 'De 09:00 AM a 10:00 AM', label: '9:00 AM - 10:00 AM' },
    { value: 'De 10:00 AM a 11:00 AM', label: '10:00 AM - 11:00 AM' },
    { value: 'De 11:00 AM a 12:00 PM', label: '11:00 AM - 12:00 PM' },
    { value: 'De 12:00 PM a 01:00 PM', label: '12:00 PM - 1:00 PM' },
    { value: 'De 01:00 PM a 02:00 PM', label: '1:00 PM - 2:00 PM' },
    { value: 'De 02:00 PM a 03:00 PM', label: '2:00 PM - 3:00 PM' },
    { value: 'De 03:00 PM a 04:00 PM', label: '3:00 PM - 4:00 PM' },
    { value: 'De 04:00 PM a 05:00 PM', label: '4:00 PM - 5:00 PM' },
    { value: 'De 05:00 PM a 06:00 PM', label: '5:00 PM - 6:00 PM' },
    { value: 'De 06:00 PM a 07:00 PM', label: '6:00 PM - 7:00 PM' },
    { value: 'De 07:00 PM a 08:00 PM', label: '7:00 PM - 8:00 PM' },
  ];

  const courtOptions = [
    { value: '1', label: 'Court 1' },
    { value: '2', label: 'Court 2' },
  ];

  const surfaceOptions = [
    { value: 'hard', label: 'Hard Court' },
    { value: 'clay', label: 'Clay Court' },
    { value: 'grass', label: 'Grass Court' },
  ];

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!validateRequired(formData.club_name)) {
      newErrors.club_name = 'Club name is required';
    }

    if (!validateRequired(formData.location)) {
      newErrors.location = 'Location is required';
    }

    if (!validateRequired(formData.username)) {
      newErrors.username = 'Username is required';
    }

    if (!validateRequired(formData.password)) {
      newErrors.password = 'Password is required';
    }

    if (formData.notification_email && !validateEmail(formData.notification_email)) {
      newErrors.notification_email = 'Please enter a valid email address';
    }

    if (formData.preferred_times.length === 0) {
      newErrors.preferred_times = 'Please select at least one preferred time';
    }

    if (formData.court_preferences.length === 0) {
      newErrors.court_preferences = 'Please select at least one court preference';
    }

    if (formData.booking_advance_days < 1 || formData.booking_advance_days > 30) {
      newErrors.booking_advance_days = 'Booking advance days must be between 1 and 30';
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
      await onSave(formData);
    } catch (err) {
      console.error('Configuration save failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof TennisConfig) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const value = e.target.type === 'checkbox' 
      ? (e.target as HTMLInputElement).checked 
      : e.target.value;
    
    setFormData(prev => ({
      ...prev,
      [field]: field === 'booking_advance_days' ? parseInt(value as string) : value,
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleMultiSelect = (field: 'preferred_times' | 'court_preferences') => (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const value = e.target.value;
    const currentValues = formData[field] as string[];
    
    const newValues = currentValues.includes(value)
      ? currentValues.filter(v => v !== value)
      : [...currentValues, value];
    
    setFormData(prev => ({
      ...prev,
      [field]: newValues,
    }));
    
    // Clear error when user makes selection
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <Card className={cn('w-full max-w-2xl mx-auto', className)} variant="court">
      <CardHeader>
        <CardTitle className="text-2xl font-bold flex items-center">
          <span className="mr-3">⚙️</span>
          Tennis Court Configuration
        </CardTitle>
        <p className="text-muted-foreground">
          Configure your tennis court booking preferences and credentials
        </p>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200">
              <p className="text-sm text-red-700 flex items-center">
                <span className="mr-2">⚠️</span>
                {error}
              </p>
            </div>
          )}

          {/* Club Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Club Information</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Club Name"
                value={formData.club_name}
                onChange={handleInputChange('club_name')}
                error={errors.club_name}
                placeholder="e.g., Tennis Club Barcelona"
                variant="court"
                fullWidth
                required
              />

              <Input
                label="Location"
                value={formData.location}
                onChange={handleInputChange('location')}
                error={errors.location}
                placeholder="e.g., Barcelona, Spain"
                variant="court"
                fullWidth
                required
              />
            </div>
          </div>

          {/* Account Credentials */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Account Credentials</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Username"
                value={formData.username}
                onChange={handleInputChange('username')}
                error={errors.username}
                placeholder="Your tennis website username"
                variant="court"
                fullWidth
                required
              />

              <Input
                label="Password"
                type="password"
                value={formData.password}
                onChange={handleInputChange('password')}
                error={errors.password}
                placeholder="Your tennis website password"
                variant="court"
                fullWidth
                required
              />
            </div>
          </div>

          {/* Booking Preferences */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Booking Preferences</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Preferred Times <span className="text-red-500">*</span>
                </label>
                <div className="space-y-2 max-h-40 overflow-y-auto border border-border rounded-md p-3">
                  {timeSlotOptions.map((option) => (
                    <label key={option.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.preferred_times.includes(option.value)}
                        onChange={() => {
                          const newTimes = formData.preferred_times.includes(option.value)
                            ? formData.preferred_times.filter(t => t !== option.value)
                            : [...formData.preferred_times, option.value];
                          
                          setFormData(prev => ({
                            ...prev,
                            preferred_times: newTimes,
                          }));
                        }}
                        className="rounded border-border"
                      />
                      <span className="text-sm">{option.label}</span>
                    </label>
                  ))}
                </div>
                {errors.preferred_times && (
                  <p className="text-sm text-red-500 mt-1">{errors.preferred_times}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Court Preferences <span className="text-red-500">*</span>
                </label>
                <div className="space-y-2 border border-border rounded-md p-3">
                  {courtOptions.map((option) => (
                    <label key={option.value} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={formData.court_preferences.includes(option.value)}
                        onChange={() => {
                          const newCourts = formData.court_preferences.includes(option.value)
                            ? formData.court_preferences.filter(c => c !== option.value)
                            : [...formData.court_preferences, option.value];
                          
                          setFormData(prev => ({
                            ...prev,
                            court_preferences: newCourts,
                          }));
                        }}
                        className="rounded border-border"
                      />
                      <span className="text-sm">{option.label}</span>
                    </label>
                  ))}
                </div>
                {errors.court_preferences && (
                  <p className="text-sm text-red-500 mt-1">{errors.court_preferences}</p>
                )}
              </div>
            </div>
          </div>

          {/* Additional Settings */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-foreground">Additional Settings</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Booking Advance Days"
                type="number"
                value={formData.booking_advance_days.toString()}
                onChange={handleInputChange('booking_advance_days')}
                error={errors.booking_advance_days}
                min="1"
                max="30"
                variant="court"
                fullWidth
                required
              />

              <Select
                label="Court Surface"
                value={formData.court_surface}
                onChange={handleInputChange('court_surface')}
                options={surfaceOptions}
                variant="court"
                fullWidth
              />

              <Input
                label="Notification Email"
                type="email"
                value={formData.notification_email}
                onChange={handleInputChange('notification_email')}
                error={errors.notification_email}
                placeholder="your@email.com"
                variant="court"
                fullWidth
              />
            </div>
          </div>

          {/* Auto-booking toggle */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="auto_book"
              checked={formData.auto_book}
              onChange={handleInputChange('auto_book')}
              className="rounded border-border"
            />
            <label htmlFor="auto_book" className="text-sm font-medium text-foreground">
              Enable automatic booking when slots become available
            </label>
          </div>

          <div className="pt-4 border-t border-border">
            <Button
              type="submit"
              variant="court-green"
              size="lg"
              fullWidth
              loading={isSubmitting || loading}
              disabled={isSubmitting || loading}
            >
              {isSubmitting || loading ? 'Saving Configuration...' : 'Save Configuration'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export { ConfigurationForm };
export type { ConfigurationFormProps };