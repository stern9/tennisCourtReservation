// ABOUTME: Main page component for the tennis court reservation system
// ABOUTME: Clean, simplified design with login, dashboard, and booking views

'use client';

import { useState, useEffect } from 'react';
import { Dashboard } from '@/components/layout';
import { LoginForm, BookingForm } from '@/components/forms';
import { Card, CardContent, CardHeader, CardTitle, Button } from '@/components/ui';
import { useTennisStore } from '@/store';
import { useConfig, useBookings, useCourtStatus } from '@/hooks/useApi';
import { cn } from '@/lib/utils';

// Utility function to format dates with day names
const formatDateWithDay = (dateString: string): string => {
  const date = new Date(dateString);
  const dayName = date.toLocaleDateString('en-US', { weekday: 'long' });
  const day = date.getDate();
  const month = date.toLocaleDateString('en-US', { month: 'long' });
  
  // Add ordinal suffix
  const ordinalSuffix = (day: number): string => {
    if (day > 3 && day < 21) return 'th';
    switch (day % 10) {
      case 1: return 'st';
      case 2: return 'nd';
      case 3: return 'rd';
      default: return 'th';
    }
  };
  
  return `${dayName}, ${month} ${day}${ordinalSuffix(day)}`;
};

// Auto-reservation interface
interface AutoReservation {
  id: string;
  court_name: string;
  preferred_time: string;
  target_date: string;
  auto_book_at: string;
  status: 'scheduled' | 'attempting';
}

export default function Home() {
  const { 
    config, 
    isConfigured, 
    setConfig, 
    clearConfig, 
    currentView, 
    setCurrentView,
    error,
    setError,
    bookingRequests 
  } = useTennisStore();
  
  const { saveConfig } = useConfig();
  const { createBooking, loading: bookingLoading } = useBookings();

  const [user, setUser] = useState<{ username: string; email: string } | null>(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [autoReservations, setAutoReservations] = useState<AutoReservation[]>([]);

  // Set user from config
  useEffect(() => {
    if (config) {
      setUser({
        username: config.username,
        email: config.notification_email || `${config.username}@tennis.com`,
      });
    }
  }, [config]);

  // Add sample data for testing when user logs in
  useEffect(() => {
    if (isConfigured && bookingRequests.length === 0) {
      // Add sample current reservations (already booked)
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(today.getDate() + 1);
      const dayAfter = new Date(today);
      dayAfter.setDate(today.getDate() + 2);
      
      const sampleBookings = [
        {
          id: '1',
          court_name: 'Court 1',
          date: tomorrow.toISOString().split('T')[0],
          time: 'De 09:00 AM a 10:00 AM',
          duration: 60,
          status: 'confirmed' as const,
          created_at: new Date().toISOString(),
          user_id: 'current_user',
        },
        {
          id: '2',
          court_name: 'Court 2',
          date: dayAfter.toISOString().split('T')[0],
          time: 'De 02:00 PM a 03:00 PM',
          duration: 60,
          status: 'pending' as const,
          created_at: new Date().toISOString(),
          user_id: 'current_user',
        },
      ];

      // Add sample bookings to store
      sampleBookings.forEach(booking => {
        useTennisStore.getState().addBookingRequest(booking);
      });

      // Add sample auto-reservations (future booking attempts)
      const nextWeek = new Date(today);
      nextWeek.setDate(today.getDate() + 7);
      const nextWeekPlus1 = new Date(today);
      nextWeekPlus1.setDate(today.getDate() + 8);
      const bookingDay = new Date(today);
      bookingDay.setDate(today.getDate() + 1); // booking opens tomorrow
      
      const sampleAutoReservations: AutoReservation[] = [
        {
          id: 'auto-1',
          court_name: 'Court 1',
          preferred_time: '09:00 AM - 10:00 AM',
          target_date: nextWeek.toISOString().split('T')[0],
          auto_book_at: `${bookingDay.toISOString().split('T')[0]} 12:00 PM`,
          status: 'scheduled',
        },
        {
          id: 'auto-2',
          court_name: 'Court 2',
          preferred_time: '02:00 PM - 03:00 PM',
          target_date: nextWeekPlus1.toISOString().split('T')[0],
          auto_book_at: `${dayAfter.toISOString().split('T')[0]} 12:00 PM`,
          status: 'attempting',
        },
      ];

      setAutoReservations(sampleAutoReservations);
    }
  }, [isConfigured, bookingRequests.length]);

  const handleLogin = async (credentials: { username: string; password: string }) => {
    setAuthLoading(true);
    setError(null);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Create simple config with just credentials
      const simpleConfig = {
        username: credentials.username,
        password: credentials.password,
        notification_email: `${credentials.username}@tennis.com`,
        // Default values for required fields
        club_name: 'Tennis Club',
        location: 'Local',
        preferred_times: ['De 09:00 AM a 10:00 AM'],
        court_preferences: ['1'],
        booking_advance_days: 7,
        auto_book: false,
        court_surface: 'hard' as const,
      };
      
      await saveConfig(simpleConfig);
      setConfig(simpleConfig);
      setCurrentView('dashboard');
    } catch (err) {
      setError('Login failed. Please check your credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    clearConfig();
    setUser(null);
    setCurrentView('login');
  };

  const handleBookingSubmit = async (bookingData: any) => {
    try {
      await createBooking(bookingData);
      setCurrentView('dashboard');
    } catch (err) {
      setError('Failed to create booking. Please try again.');
    }
  };

  // Show login if not configured
  if (!isConfigured || currentView === 'login') {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <LoginForm
          onLogin={handleLogin}
          loading={authLoading}
          error={error}
        />
      </div>
    );
  }

  // Show booking form
  if (currentView === 'booking') {
    return (
      <Dashboard user={user} onLogout={handleLogout}>
        <div className="max-w-2xl mx-auto">
          <div className="mb-4">
            <Button
              variant="outline"
              onClick={() => setCurrentView('dashboard')}
              className="mb-4"
            >
              ← Back to Dashboard
            </Button>
          </div>
          <BookingForm
            onSubmit={handleBookingSubmit}
            loading={bookingLoading}
            error={error}
          />
        </div>
      </Dashboard>
    );
  }

  // Main dashboard view
  return (
    <Dashboard user={user} onLogout={handleLogout}>
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
            Tennis Court Reservations
          </h1>
          <p className="text-gray-600">
            Manage your court bookings
          </p>
        </div>

        {/* Current Reservations */}
        <Card>
          <CardHeader>
            <CardTitle>Current Reservations</CardTitle>
          </CardHeader>
          <CardContent>
            {bookingRequests.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">No active reservations</p>
                <Button
                  variant="court-green"
                  onClick={() => setCurrentView('booking')}
                >
                  Create Your First Booking
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {bookingRequests.map((booking) => (
                  <div 
                    key={booking.id} 
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 bg-white rounded-lg border space-y-2 sm:space-y-0"
                  >
                    <div>
                      <div className="font-semibold text-gray-900">
                        {booking.court_name}
                      </div>
                      <div className="text-sm text-gray-600">
                        {formatDateWithDay(booking.date)} at {booking.time.replace('De ', '').replace(' a ', ' - ')}
                      </div>
                      <div className="text-xs text-gray-500">
                        Duration: {booking.duration} minutes
                      </div>
                    </div>
                    <div className={cn(
                      'px-3 py-1 rounded-full text-sm font-medium self-start sm:self-center',
                      booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                      booking.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    )}>
                      {booking.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Scheduled Auto-Reservations */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Auto-Bookings</CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              Automatic booking attempts scheduled for future dates
            </p>
          </CardHeader>
          <CardContent>
            {autoReservations.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500 mb-4">
                  No auto-bookings scheduled
                </p>
                <p className="text-sm text-gray-400">
                  Set up automatic booking attempts for popular time slots
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {autoReservations.map((reservation) => (
                  <div 
                    key={reservation.id} 
                    className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-4 bg-blue-50 rounded-lg border border-blue-200 space-y-2 sm:space-y-0"
                  >
                    <div>
                      <div className="font-semibold text-gray-900">
                        {reservation.court_name}
                      </div>
                      <div className="text-sm text-gray-600">
                        Target: {formatDateWithDay(reservation.target_date)} at {reservation.preferred_time}
                      </div>
                      <div className="text-xs text-gray-500">
                        Will attempt booking on: {formatDateWithDay(reservation.auto_book_at.split(' ')[0])} at {reservation.auto_book_at.split(' ')[1]} {reservation.auto_book_at.split(' ')[2]}
                      </div>
                    </div>
                    <div className={cn(
                      'px-3 py-1 rounded-full text-sm font-medium self-start sm:self-center',
                      reservation.status === 'scheduled' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    )}>
                      {reservation.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* New Booking Button */}
        <div className="flex justify-center">
          <Button
            variant="court-green"
            size="lg"
            onClick={() => setCurrentView('booking')}
            className="px-8"
          >
            🎾 New Booking
          </Button>
        </div>
      </div>
    </Dashboard>
  );
}