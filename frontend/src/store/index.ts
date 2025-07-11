// ABOUTME: Main application store using Zustand for state management
// ABOUTME: Manages tennis court reservation configuration and booking state

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// Types
export interface TennisConfig {
  club_name: string;
  location: string;
  username: string;
  password: string;
  preferred_times: string[];
  court_preferences: string[];
  booking_advance_days: number;
  auto_book: boolean;
  notification_email: string;
  court_surface: 'clay' | 'hard' | 'grass';
}

export interface BookingRequest {
  id: string;
  court_name: string;
  date: string;
  time: string;
  duration: number;
  status: 'pending' | 'confirmed' | 'failed' | 'cancelled';
  created_at: string;
  user_id: string;
}

export interface CourtStatus {
  court_name: string;
  available_times: string[];
  occupied_times: string[];
  surface: 'clay' | 'hard' | 'grass';
  last_updated: string;
}

// Store State Interface
interface TennisStoreState {
  // Configuration
  config: TennisConfig | null;
  isConfigured: boolean;
  
  // Booking State
  bookingRequests: BookingRequest[];
  currentBookings: BookingRequest[];
  courtStatus: CourtStatus[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
  currentView: 'config' | 'dashboard' | 'booking' | 'status';
  
  // Actions
  setConfig: (config: TennisConfig) => void;
  clearConfig: () => void;
  addBookingRequest: (request: BookingRequest) => void;
  updateBookingRequest: (id: string, updates: Partial<BookingRequest>) => void;
  removeBookingRequest: (id: string) => void;
  updateCourtStatus: (status: CourtStatus[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCurrentView: (view: 'config' | 'dashboard' | 'booking' | 'status') => void;
  refreshData: () => Promise<void>;
}

// Default configuration
const defaultConfig: TennisConfig = {
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
};

// Create the store
export const useTennisStore = create<TennisStoreState>()(
  persist(
    (set, get) => ({
      // Initial State
      config: null,
      isConfigured: false,
      bookingRequests: [],
      currentBookings: [],
      courtStatus: [],
      isLoading: false,
      error: null,
      currentView: 'config',

      // Actions
      setConfig: (config: TennisConfig) => {
        set({
          config,
          isConfigured: true,
          currentView: 'dashboard',
          error: null,
        });
      },

      clearConfig: () => {
        set({
          config: null,
          isConfigured: false,
          currentView: 'config',
          bookingRequests: [],
          currentBookings: [],
          courtStatus: [],
          error: null,
        });
      },

      addBookingRequest: (request: BookingRequest) => {
        set((state) => ({
          bookingRequests: [...state.bookingRequests, request],
        }));
      },

      updateBookingRequest: (id: string, updates: Partial<BookingRequest>) => {
        set((state) => ({
          bookingRequests: state.bookingRequests.map((req) =>
            req.id === id ? { ...req, ...updates } : req
          ),
          currentBookings: state.currentBookings.map((req) =>
            req.id === id ? { ...req, ...updates } : req
          ),
        }));
      },

      removeBookingRequest: (id: string) => {
        set((state) => ({
          bookingRequests: state.bookingRequests.filter((req) => req.id !== id),
          currentBookings: state.currentBookings.filter((req) => req.id !== id),
        }));
      },

      updateCourtStatus: (status: CourtStatus[]) => {
        set({ courtStatus: status });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error });
      },

      setCurrentView: (view: 'config' | 'dashboard' | 'booking' | 'status') => {
        set({ currentView: view });
      },

      refreshData: async () => {
        const { config } = get();
        if (!config) return;

        set({ isLoading: true, error: null });

        try {
          // This will be implemented when we integrate with the backend API
          // For now, we'll just simulate data loading
          await new Promise((resolve) => setTimeout(resolve, 1000));
          
          // Mock data update
          const mockCourtStatus: CourtStatus[] = [
            {
              court_name: 'Court 1',
              available_times: ['09:00', '10:00', '11:00', '14:00', '15:00'],
              occupied_times: ['08:00', '12:00', '13:00', '16:00'],
              surface: config.court_surface,
              last_updated: new Date().toISOString(),
            },
            {
              court_name: 'Court 2',
              available_times: ['08:00', '09:00', '13:00', '14:00', '15:00'],
              occupied_times: ['10:00', '11:00', '12:00', '16:00'],
              surface: config.court_surface,
              last_updated: new Date().toISOString(),
            },
          ];

          set({ courtStatus: mockCourtStatus });
        } catch (error) {
          set({ error: 'Failed to refresh data' });
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'tennis-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        config: state.config,
        isConfigured: state.isConfigured,
        bookingRequests: state.bookingRequests,
        currentBookings: state.currentBookings,
      }),
    }
  )
);

// Selector hooks for specific state slices
export const useConfig = () => useTennisStore((state) => state.config);
export const useIsConfigured = () => useTennisStore((state) => state.isConfigured);
export const useBookingRequests = () => useTennisStore((state) => state.bookingRequests);
export const useCurrentBookings = () => useTennisStore((state) => state.currentBookings);
export const useCourtStatus = () => useTennisStore((state) => state.courtStatus);
export const useIsLoading = () => useTennisStore((state) => state.isLoading);
export const useError = () => useTennisStore((state) => state.error);
export const useCurrentView = () => useTennisStore((state) => state.currentView);