// ABOUTME: Calendar component for date selection with tennis court availability
// ABOUTME: Displays available dates and handles date selection for bookings

import { useState } from 'react';
import { cn, formatDate, isToday, getDateRange } from '@/lib/utils';
import { Button } from './Button';

interface CalendarProps {
  selectedDate?: Date;
  onDateSelect?: (date: Date) => void;
  availableDates?: Date[];
  disabledDates?: Date[];
  minDate?: Date;
  maxDate?: Date;
  className?: string;
  bookingAdvanceDays?: number; // How many days in advance booking opens
}

const Calendar = ({
  selectedDate,
  onDateSelect,
  availableDates,
  disabledDates = [],
  minDate,
  maxDate,
  className,
  bookingAdvanceDays = 7,
}: CalendarProps) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());

  const today = new Date();
  const startOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
  const endOfMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);
  const startOfWeek = new Date(startOfMonth);
  startOfWeek.setDate(startOfMonth.getDate() - startOfMonth.getDay());

  const daysInView = getDateRange(startOfWeek, 42); // 6 weeks

  const isDateDisabled = (date: Date): boolean => {
    if (minDate && date < minDate) return true;
    if (maxDate && date > maxDate) return true;
    return disabledDates.some(disabled => 
      date.toDateString() === disabled.toDateString()
    );
  };

  const isDateAvailable = (date: Date): boolean => {
    if (!availableDates) return true;
    return availableDates.some(available => 
      date.toDateString() === available.toDateString()
    );
  };

  // Determine the type of date for booking logic
  const getDateType = (date: Date): 'past' | 'ready' | 'auto' => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const targetDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    // Past dates or today
    if (targetDate <= today) {
      return 'past';
    }
    
    // Calculate when booking opens for this date
    const bookingOpensDate = new Date(targetDate);
    bookingOpensDate.setDate(targetDate.getDate() - bookingAdvanceDays);
    
    // If booking has already opened, it's ready to book
    if (today >= bookingOpensDate) {
      return 'ready';
    }
    
    // If booking hasn't opened yet, it requires auto-booking
    return 'auto';
  };

  const isDateSelected = (date: Date): boolean => {
    if (!selectedDate) return false;
    return date.toDateString() === selectedDate.toDateString();
  };

  const handleDateClick = (date: Date) => {
    const dateType = getDateType(date);
    if (dateType === 'past' || isDateDisabled(date) || !isDateAvailable(date)) return;
    onDateSelect?.(date);
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newMonth = new Date(currentMonth);
    if (direction === 'prev') {
      newMonth.setMonth(newMonth.getMonth() - 1);
    } else {
      newMonth.setMonth(newMonth.getMonth() + 1);
    }
    setCurrentMonth(newMonth);
  };

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className={cn('p-4 bg-background border border-border rounded-lg', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigateMonth('prev')}
          className="p-2"
        >
          ←
        </Button>
        <h2 className="text-lg font-semibold">
          {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
        </h2>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigateMonth('next')}
          className="p-2"
        >
          →
        </Button>
      </div>

      {/* Days of the week */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {dayNames.map(day => (
          <div
            key={day}
            className="text-center text-sm font-medium text-muted-foreground p-2"
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {daysInView.map((date, index) => {
          const isCurrentMonth = date.getMonth() === currentMonth.getMonth();
          const isDisabled = isDateDisabled(date);
          const isSelected = isDateSelected(date);
          const isTodayDate = isToday(date);
          const dateType = getDateType(date);

          return (
            <button
              key={index}
              onClick={() => handleDateClick(date)}
              disabled={dateType === 'past' || isDisabled}
              className={cn(
                'h-10 w-10 rounded-md text-sm font-medium transition-colors',
                'hover:bg-muted focus:bg-muted focus:outline-none',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                {
                  'text-muted-foreground': !isCurrentMonth,
                  'bg-court-green text-court-line': isSelected,
                  'bg-blue-100 text-blue-800': isTodayDate && !isSelected,
                  // Color coding based on date type
                  'bg-green-100 text-green-800 hover:bg-green-200': dateType === 'ready' && !isSelected && !isTodayDate && isCurrentMonth,
                  'bg-purple-100 text-purple-800 hover:bg-purple-200': dateType === 'auto' && !isSelected && !isTodayDate && isCurrentMonth,
                  'bg-red-100 text-red-800': dateType === 'past' && isCurrentMonth,
                }
              )}
            >
              {date.getDate()}
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 flex flex-wrap gap-3 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-100 border border-green-200 rounded"></div>
          <span>Book Now</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-purple-100 border border-purple-200 rounded"></div>
          <span>Auto-Schedule</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-red-100 border border-red-200 rounded"></div>
          <span>Past/Unavailable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-court-green rounded"></div>
          <span>Selected</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-blue-100 border border-blue-200 rounded"></div>
          <span>Today</span>
        </div>
      </div>
    </div>
  );
};

export { Calendar };
export type { CalendarProps };