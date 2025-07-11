// ABOUTME: Simplified booking form for creating tennis court reservations
// ABOUTME: Clean 3-field form with court, date, and time selection (1-hour fixed duration)

'use client';

import { useState } from 'react';
import { Button, Card, CardContent, CardHeader, CardTitle, Select, Calendar } from '@/components/ui';
import { validateRequired, cn, formatDate, isFuture, getDateRange } from '@/lib/utils';
import { BookingRequest } from '@/store';

interface BookingFormProps {
  onSubmit: (booking: Omit<BookingRequest, 'id' | 'created_at' | 'status'>) => Promise<void>;
  loading?: boolean;
  error?: string;
  className?: string;
}

interface BookingFormData {
  court_name: string;
  date: string;
  time: string;
}

interface FormErrors {
  [key: string]: string | undefined;
}

const BookingForm = ({ 
  onSubmit, 
  loading = false, 
  error, 
  className 
}: BookingFormProps) => {
  const [formData, setFormData] = useState<BookingFormData>({
    court_name: '',
    date: '',
    time: '',
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>();

  // Available courts (only 2 courts)
  const courtOptions = [
    { value: '1', label: 'Court 1' },
    { value: '2', label: 'Court 2' },
  ];

  // Available time slots (1-hour slots)
  const timeOptions = [
    { value: 'De 08:00 AM a 09:00 AM', label: '08:00 AM - 09:00 AM' },
    { value: 'De 09:00 AM a 10:00 AM', label: '09:00 AM - 10:00 AM' },
    { value: 'De 10:00 AM a 11:00 AM', label: '10:00 AM - 11:00 AM' },
    { value: 'De 11:00 AM a 12:00 PM', label: '11:00 AM - 12:00 PM' },
    { value: 'De 12:00 PM a 01:00 PM', label: '12:00 PM - 01:00 PM' },
    { value: 'De 01:00 PM a 02:00 PM', label: '01:00 PM - 02:00 PM' },
    { value: 'De 02:00 PM a 03:00 PM', label: '02:00 PM - 03:00 PM' },
    { value: 'De 03:00 PM a 04:00 PM', label: '03:00 PM - 04:00 PM' },
    { value: 'De 04:00 PM a 05:00 PM', label: '04:00 PM - 05:00 PM' },
    { value: 'De 05:00 PM a 06:00 PM', label: '05:00 PM - 06:00 PM' },
    { value: 'De 06:00 PM a 07:00 PM', label: '06:00 PM - 07:00 PM' },
    { value: 'De 07:00 PM a 08:00 PM', label: '07:00 PM - 08:00 PM' },
  ];

  // Generate available dates for the next 30 days
  const availableDates = getDateRange(new Date(), 30).filter(date => isFuture(date));

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!validateRequired(formData.court_name)) {
      newErrors.court_name = 'Please select a court';
    }

    if (!validateRequired(formData.date)) {
      newErrors.date = 'Please select a date';
    }

    if (!validateRequired(formData.time)) {
      newErrors.time = 'Please select a time';
    }

    // Check if selected date is in the future
    if (formData.date && !isFuture(new Date(formData.date))) {
      newErrors.date = 'Please select a future date';
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
      const bookingRequest: Omit<BookingRequest, 'id' | 'created_at' | 'status'> = {
        court_name: `Court ${formData.court_name}`,
        date: formData.date,
        time: formData.time,
        duration: 60, // Fixed 1-hour duration
        user_id: 'current_user',
      };
      
      await onSubmit(bookingRequest);
      
      // Reset form on success
      setFormData({
        court_name: '',
        date: '',
        time: '',
      });
      setSelectedDate(undefined);
      
    } catch (err) {
      console.error('Booking creation failed:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof BookingFormData) => (
    e: React.ChangeEvent<HTMLSelectElement>
  ) => {
    const value = e.target.value;
    
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Clear error when user selects
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  const handleDateSelect = (date: Date) => {
    setSelectedDate(date);
    setFormData(prev => ({
      ...prev,
      date: date.toISOString().split('T')[0],
    }));
    
    // Clear date error
    if (errors.date) {
      setErrors(prev => ({
        ...prev,
        date: undefined,
      }));
    }
  };

  // Check if selected date requires auto-scheduling
  const getDateType = (date: Date): 'past' | 'ready' | 'auto' => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    if (targetDate <= today) return 'past';
    
    const bookingOpensDate = new Date(targetDate);
    bookingOpensDate.setDate(targetDate.getDate() - 7); // 7 days advance
    
    if (today >= bookingOpensDate) return 'ready';
    return 'auto';
  };

  const selectedDateType = formData.date ? getDateType(new Date(formData.date)) : null;

  return (
    <Card className={cn('w-full max-w-lg mx-auto', className)}>
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-bold">
          🎾 New Booking
        </CardTitle>
        <p className="text-muted-foreground">
          Reserve your tennis court for 1 hour
        </p>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 rounded-md bg-red-50 border border-red-200">
              <p className="text-sm text-red-700">
                {error}
              </p>
            </div>
          )}

          {/* Court Selection */}
          <Select
            label="Court"
            value={formData.court_name}
            onChange={handleInputChange('court_name')}
            options={courtOptions}
            placeholder="Select a court"
            error={errors.court_name}
            fullWidth
            required
          />

          {/* Date Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Date</label>
            <Calendar
              selectedDate={selectedDate}
              onDateSelect={handleDateSelect}
              availableDates={availableDates}
              minDate={new Date()}
              bookingAdvanceDays={7}
              className="mx-auto"
            />
            {errors.date && (
              <p className="text-sm text-red-500 text-center">{errors.date}</p>
            )}
          </div>

          {/* Time Selection */}
          <Select
            label="Time"
            value={formData.time}
            onChange={handleInputChange('time')}
            options={timeOptions}
            placeholder="Select a time slot"
            error={errors.time}
            fullWidth
            required
          />

          {/* Booking Summary */}
          {formData.court_name && formData.date && formData.time && (
            <div className="p-4 rounded-lg bg-gray-50 border">
              <h4 className="font-semibold mb-2">Booking Summary</h4>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Court:</span>
                  <span>Court {formData.court_name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Date:</span>
                  <span>{formatDate(formData.date)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Time:</span>
                  <span>{formData.time.replace('De ', '').replace(' a ', ' - ')}</span>
                </div>
                <div className="flex justify-between">
                  <span>Duration:</span>
                  <span>1 Hour</span>
                </div>
              </div>
            </div>
          )}

          {selectedDateType === 'auto' && (
            <div className="p-3 rounded-md bg-purple-50 border border-purple-200 mb-4">
              <p className="text-sm text-purple-800">
                <strong>Auto-Schedule Required:</strong> This date requires automatic booking since booking hasn't opened yet. 
                We'll attempt to book this slot when booking opens.
              </p>
            </div>
          )}

          <Button
            type="submit"
            variant={selectedDateType === 'auto' ? 'outline' : 'court-green'}
            size="lg"
            fullWidth
            loading={isSubmitting || loading}
            disabled={isSubmitting || loading}
          >
            {isSubmitting || loading ? 
              (selectedDateType === 'auto' ? 'Scheduling Auto-Booking...' : 'Creating Booking...') : 
              (selectedDateType === 'auto' ? 'Schedule Auto-Booking' : 'Create Booking')
            }
          </Button>
        </form>
      </CardContent>
    </Card>
  );
};

export { BookingForm };
export type { BookingFormProps };