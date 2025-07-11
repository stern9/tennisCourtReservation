// ABOUTME: Custom React hooks for API integration and data fetching
// ABOUTME: Provides convenient hooks for tennis court booking operations

import { useState, useEffect, useCallback } from 'react';
import { apiService, handleApiError } from '@/lib/api';
import { useTennisStore } from '@/store';
import { TennisConfig, BookingRequest, CourtStatus } from '@/store';

// Generic API hook
export const useApi = <T>(
  apiCall: () => Promise<T>,
  deps: any[] = [],
  immediate = true
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { data, loading, error, execute, refetch: execute };
};

// Configuration hooks
export const useConfig = () => {
  const { setConfig, setError } = useTennisStore();
  const [loading, setLoading] = useState(false);

  const loadConfig = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getConfig();
      if (response.is_configured) {
        setConfig(response.config);
      }
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setConfig, setError]);

  const saveConfig = useCallback(async (config: TennisConfig) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.saveConfig(config);
      setConfig(response.config);
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setConfig, setError]);

  const updateConfig = useCallback(async (updates: Partial<TennisConfig>) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.updateConfig(updates);
      setConfig(response.config);
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setConfig, setError]);

  return {
    loading,
    loadConfig,
    saveConfig,
    updateConfig,
  };
};

// Booking hooks
export const useBookings = () => {
  const { 
    bookingRequests, 
    addBookingRequest, 
    updateBookingRequest, 
    removeBookingRequest,
    setError 
  } = useTennisStore();
  const [loading, setLoading] = useState(false);

  const loadBookings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const bookings = await apiService.getBookings();
      // Update store with fetched bookings
      bookings.forEach(booking => {
        const existingBooking = bookingRequests.find(b => b.id === booking.id);
        if (existingBooking) {
          updateBookingRequest(booking.id, booking);
        } else {
          addBookingRequest(booking);
        }
      });
      return bookings;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [bookingRequests, addBookingRequest, updateBookingRequest, setError]);

  const createBooking = useCallback(async (booking: Omit<BookingRequest, 'id' | 'created_at'>) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.createBooking(booking);
      
      // Add the booking to the store with pending status
      const newBooking: BookingRequest = {
        ...booking,
        id: response.booking_id,
        status: 'pending',
        created_at: new Date().toISOString(),
      };
      addBookingRequest(newBooking);
      
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [addBookingRequest, setError]);

  const cancelBooking = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const updatedBooking = await apiService.cancelBooking(id);
      updateBookingRequest(id, updatedBooking);
      return updatedBooking;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [updateBookingRequest, setError]);

  const deleteBooking = useCallback(async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      await apiService.deleteBooking(id);
      removeBookingRequest(id);
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [removeBookingRequest, setError]);

  return {
    bookings: bookingRequests,
    loading,
    loadBookings,
    createBooking,
    cancelBooking,
    deleteBooking,
  };
};

// Court status hooks
export const useCourtStatus = () => {
  const { courtStatus, updateCourtStatus, setError } = useTennisStore();
  const [loading, setLoading] = useState(false);

  const loadCourtStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getCourtStatus();
      updateCourtStatus(response.courts);
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [updateCourtStatus, setError]);

  const refreshCourtStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.refreshCourtStatus();
      updateCourtStatus(response.courts);
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [updateCourtStatus, setError]);

  return {
    courtStatus,
    loading,
    loadCourtStatus,
    refreshCourtStatus,
  };
};

// Tennis automation hooks
export const useTennisAutomation = () => {
  const { setError } = useTennisStore();
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [lastRun, setLastRun] = useState<string>('');

  const runAutomation = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.runTennisAutomation();
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setError]);

  const loadLogs = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.getTennisLogs();
      setLogs(response.logs);
      setLastRun(response.last_run);
      return response;
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [setError]);

  return {
    loading,
    logs,
    lastRun,
    runAutomation,
    loadLogs,
  };
};

// Health check hook
export const useHealthCheck = (interval: number = 30000) => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const healthy = await apiService.healthCheck();
      setIsHealthy(healthy);
      setLastCheck(new Date());
      return healthy;
    } catch (err) {
      setIsHealthy(false);
      setLastCheck(new Date());
      return false;
    }
  }, []);

  useEffect(() => {
    // Initial check
    checkHealth();

    // Set up interval for periodic checks
    const intervalId = setInterval(checkHealth, interval);

    return () => clearInterval(intervalId);
  }, [checkHealth, interval]);

  return {
    isHealthy,
    lastCheck,
    checkHealth,
  };
};

// Combined hook for dashboard data
export const useDashboardData = () => {
  const { refreshData } = useTennisStore();
  const { loadBookings } = useBookings();
  const { loadCourtStatus } = useCourtStatus();
  const [loading, setLoading] = useState(false);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadBookings(),
        loadCourtStatus(),
      ]);
    } catch (err) {
      // Individual hooks handle their own errors
      throw err;
    } finally {
      setLoading(false);
    }
  }, [loadBookings, loadCourtStatus]);

  const refreshDashboardData = useCallback(async () => {
    await refreshData();
    await loadDashboardData();
  }, [refreshData, loadDashboardData]);

  return {
    loading,
    loadDashboardData,
    refreshDashboardData,
  };
};