import React, { useState, useEffect } from 'react';
import { format, addDays, isWeekend, isBefore, isSameDay } from 'date-fns';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

const WORKING_DAYS = 10; // fixed business days

const DateRangePicker = ({ onDateRangeSelect, defaultStartDate = null, defaultEndDate = null }) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedRange, setSelectedRange] = useState({ start: null, end: null });

  // ---- helpers ----
  const addWorkingDays = (date, count) => {
    let d = new Date(date);
    let added = 0;
    while (added < count) {
      d = addDays(d, 1);
      if (!isWeekend(d)) added++;
    }
    return d;
  };

  const subtractWorkingDays = (date, count) => {
    let d = new Date(date);
    let removed = 0;
    while (removed < count) {
      d = addDays(d, -1);
      if (!isWeekend(d)) removed++;
    }
    return d;
  };

  const countWorkingDays = (start, end) => {
    if (!start || !end) return 0;
    let d = new Date(start);
    let working = 0;
    while (!isAfterDay(d, end)) {
      if (!isWeekend(d)) working++;
      d = addDays(d, 1);
    }
    return working;
  };

  const isAfterDay = (a, b) => {
    return a.setHours(0,0,0,0) > b.setHours(0,0,0,0);
  };

  // ---- initial range (10 working days starting 1 week from today) ----
  useEffect(() => {
    if (defaultStartDate && defaultEndDate) {
      setSelectedRange({ start: defaultStartDate, end: defaultEndDate });
      return;
    }

    const today = new Date();
    let start = addDays(today, 7);

    // if start is weekend, push to Monday
    while (isWeekend(start)) {
      start = addDays(start, 1);
    }

    // 10 working days = start + 9 more working days
    const end = addWorkingDays(start, WORKING_DAYS - 1);
    setSelectedRange({ start, end });
    onDateRangeSelect?.({ start, end });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ---- date click: treat every click as "new END date" ----
  const handleDateClick = (date) => {
    const today = new Date();

    // block past dates + weekends
    if (isBefore(date, today) || isWeekend(date)) return;

    // clicked date is the END of the window
    const end = date;
    const start = subtractWorkingDays(end, WORKING_DAYS - 1);

    setSelectedRange({ start, end });
    onDateRangeSelect?.({ start, end });
  };

  const navigateMonth = (direction) => {
    setCurrentMonth(prev => {
      const newMonth = new Date(prev);
      newMonth.setMonth(prev.getMonth() + (direction === 'next' ? 1 : -1));
      return newMonth;
    });
  };

  const renderDays = () => {
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInLastMonth = new Date(year, month, 0).getDate();
    
    const days = [];
    const today = new Date();
    const { start, end } = selectedRange;

    const inRange = (date) => {
      if (!start || !end) return false;
      const d = date.setHours(0,0,0,0);
      const s = start.setHours(0,0,0,0);
      const e = end.setHours(0,0,0,0);
      return d >= s && d <= e;
    };

    // prev month padding
    for (let i = firstDay - 1; i >= 0; i--) {
      const day = daysInLastMonth - i;
      const date = new Date(year, month - 1, day);
      days.push({
        key: date.toISOString(),
        day,
        date,
        isCurrentMonth: false,
        isDisabled: true,
        isSelected: false,
        isInRange: false,
        isWeekend: isWeekend(date),
      });
    }

    // current month
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const disabled = isBefore(date, today) || isWeekend(date);

      const selected =
        (start && isSameDay(date, start)) || (end && isSameDay(date, end));

      days.push({
        key: date.toISOString(),
        day,
        date,
        isCurrentMonth: true,
        isDisabled: disabled,
        isSelected: selected,
        isInRange: !selected && inRange(date),
        isWeekend: isWeekend(date),
      });
    }

    // next month padding
    const daysToAdd = 42 - days.length;
    for (let i = 1; i <= daysToAdd; i++) {
      const date = new Date(year, month + 1, i);
      days.push({
        key: date.toISOString(),
        day: i,
        date,
        isCurrentMonth: false,
        isDisabled: true,
        isSelected: false,
        isInRange: false,
        isWeekend: isWeekend(date),
      });
    }

    return days;
  };

  const days = renderDays();

  const totalCalendarDays =
    selectedRange.start && selectedRange.end
      ? Math.round(
          (selectedRange.end.setHours(0,0,0,0) -
            selectedRange.start.setHours(0,0,0,0)) /
            (1000 * 60 * 60 * 24)
        ) + 1
      : 0;

  // always 10, but calculated for safety
  const workingDays = selectedRange.start && selectedRange.end
    ? countWorkingDays(selectedRange.start, selectedRange.end)
    : 0;

  return (
    <div className="bg-white/95 rounded-2xl shadow-xl border border-purple-100 px-5 py-4 max-w-md">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={() => navigateMonth('prev')}
          className="inline-flex items-center justify-center h-8 w-8 rounded-full hover:bg-purple-50 text-gray-600 transition-colors"
        >
          <ChevronLeftIcon className="h-4 w-4" />
        </button>
        <div className="flex flex-col items-center">
          <span className="text-sm font-semibold text-purple-600 tracking-wide uppercase">
            Select Date Range
          </span>
          <h3 className="text-lg font-semibold text-gray-900 -mt-0.5">
            {format(currentMonth, 'MMMM yyyy')}
          </h3>
        </div>
        <button
          onClick={() => navigateMonth('next')}
          className="inline-flex items-center justify-center h-8 w-8 rounded-full hover:bg-purple-50 text-gray-600 transition-colors"
        >
          <ChevronRightIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Week days */}
      <div className="grid grid-cols-7 gap-1 mb-1">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(label => (
          <div
            key={label}
            className="text-[0.7rem] font-semibold text-center text-gray-400 uppercase tracking-wide"
          >
            {label}
          </div>
        ))}
      </div>

      {/* Days grid */}
      <div className="grid grid-cols-7 gap-1">
        {days.map(dayData => {
          const isToday = isSameDay(dayData.date, new Date());

          let cellClasses =
            'relative flex items-center justify-center aspect-square text-sm select-none transition-all';

          if (dayData.isInRange) {
            cellClasses += ' bg-purple-50';
          }

          if (!dayData.isCurrentMonth) {
            cellClasses += ' text-gray-300';
          } else if (dayData.isDisabled) {
            cellClasses += ' text-gray-300';
          } else if (dayData.isWeekend) {
            cellClasses += ' text-gray-400';
          } else {
            cellClasses += ' text-gray-700';
          }

          if (!dayData.isDisabled) {
            cellClasses += ' cursor-pointer hover:bg-purple-50';
          } else {
            cellClasses += ' cursor-not-allowed';
          }

          let innerClasses =
            'flex items-center justify-center h-8 w-8 rounded-full';

          if (dayData.isSelected) {
            innerClasses +=
              ' bg-purple-600 text-white font-semibold shadow-sm';
          } else if (isToday && !dayData.isDisabled) {
            innerClasses +=
              ' border border-purple-400 text-purple-700 font-medium';
          }

          return (
            <div
              key={dayData.key}
              className={cellClasses}
              onClick={() => !dayData.isDisabled && handleDateClick(dayData.date)}
            >
              <div className={innerClasses}>{dayData.day}</div>
            </div>
          );
        })}
      </div>

      {/* Footer info */}
      <div className="mt-4 rounded-xl bg-purple-50/70 px-3 py-3 border border-purple-100">
        <p className="text-xs font-semibold text-purple-700 uppercase tracking-wide mb-1">
          Selected Date Range
        </p>
        <p className="text-sm text-gray-800 font-medium">
          {selectedRange.start && selectedRange.end
            ? `${format(selectedRange.start, 'MMM d, yyyy')} → ${format(
                selectedRange.end,
                'MMM d, yyyy'
              )}`
            : 'Click a date to choose the end of the window'}
        </p>
        
      </div>
    </div>
  );
};

export default DateRangePicker;
