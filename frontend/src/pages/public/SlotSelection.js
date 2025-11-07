import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { interviewService } from '../../services/interviewService';
import { CalendarDaysIcon, ClockIcon, CheckCircleIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

const SlotSelection = () => {
  const { applicationId } = useParams();
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [timesLoading, setTimesLoading] = useState(false);
  const dateSwitchTimerRef = useRef(null);
  const [viewYear, setViewYear] = useState(null);
  const [viewMonth, setViewMonth] = useState(null);

  useEffect(() => {
    const loadSlots = async () => {
      try {
        setLoading(true);
        const data = await interviewService.getAvailableSlots(applicationId);
        setSlots(data.available_slots || []);
      } catch (err) {
        if (err.response?.status === 400) {
          setError('Interview slot has already been selected for this application.');
        } else if (err.response?.status === 404) {
          setError('No available slots found. Please ensure you have a valid link or contact HR.');
        } else {
          setError('Failed to load available slots. Please try again or contact HR.');
        }
        console.error('Error loading slots:', err);
      } finally {
        setLoading(false);
      }
    };

    if (applicationId) {
      loadSlots();
    }
  }, [applicationId]);

  // Extract unique dates from slots
  const weekdayShort = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  const formatYMD = (date) => {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
  };

  const normalizeDateStr = (str) => {
    const d = new Date(str);
    return isNaN(d.getTime()) ? str : formatYMD(d);
  };

  const dates = useMemo(() => Array.from(new Set(slots.map((s) => normalizeDateStr(s.date)))), [slots]);
  const availableDateSet = useMemo(() => new Set(dates), [dates]);

  // Initialize selectedDate as the first available date
  useEffect(() => {
    if (!selectedDate && dates.length > 0) {
      setSelectedDate(dates[0]);
    }
  }, [dates, selectedDate]);

  useEffect(() => {
    // Initialize calendar month/year view based on first available date or today
    if ((viewYear === null || viewMonth === null)) {
      const baseDate = dates.length > 0 ? new Date(dates[0]) : new Date();
      setViewYear(baseDate.getFullYear());
      setViewMonth(baseDate.getMonth());
    }
  }, [dates, viewYear, viewMonth]);

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];




  const getCalendarGrid = (year, month) => {
    if (year === null || month === null) return [];
    const firstDay = new Date(year, month, 1);
    const startDay = firstDay.getDay(); // 0 (Sun) - 6 (Sat)
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const prevMonthDays = new Date(year, month, 0).getDate();

    const grid = [];
    for (let i = 0; i < 42; i++) {
      const dayNum = i - startDay + 1;
      let date;
      let inMonth = true;
      if (dayNum < 1) {
        date = new Date(year, month - 1, prevMonthDays + dayNum);
        inMonth = false;
      } else if (dayNum > daysInMonth) {
        date = new Date(year, month + 1, dayNum - daysInMonth);
        inMonth = false;
      } else {
        date = new Date(year, month, dayNum);
        inMonth = true;
      }
      grid.push({ date, inMonth, dateStr: formatYMD(date) });
    }
    return grid;
  };

  const gotoPrevMonth = () => {
    if (viewMonth === 0) {
      setViewYear((y) => (y !== null ? y - 1 : y));
      setViewMonth(11);
    } else {
      setViewMonth((m) => (m !== null ? m - 1 : m));
    }
  };

  const gotoNextMonth = () => {
    if (viewMonth === 11) {
      setViewYear((y) => (y !== null ? y + 1 : y));
      setViewMonth(0);
    } else {
      setViewMonth((m) => (m !== null ? m + 1 : m));
    }
  };

  const handleDateSelect = (date) => {
    // Clear any previous loading timer
    if (dateSwitchTimerRef.current) {
      clearTimeout(dateSwitchTimerRef.current);
    }
    
    // Show a short loading spinner while times update
    setTimesLoading(true);
    setSelectedDate(date);
    // Reset selected slot if it belongs to a different date
    if (selectedSlot && normalizeDateStr(selectedSlot.date) !== date) {
      setSelectedSlot(null);
    }
    // Hide spinner after a brief delay to provide visual feedback
    dateSwitchTimerRef.current = setTimeout(() => {
      setTimesLoading(false);
    }, 400);
  };

  const handleSlotSelect = (slot) => {
    setSelectedSlot(slot);
  };

  const handleSubmit = async () => {
    if (!selectedSlot) return;

    try {
      setSubmitting(true);
      await interviewService.selectSlot(applicationId, {
        selected_date: selectedSlot.date,
        selected_time: selectedSlot.time,
      });
      setSuccess(true);
    } catch (err) {
      if (err.response?.status === 400) {
        setError('This slot is no longer available or has already been selected.');
      } else if (err.response?.status === 404) {
        setError('Application not found. Please check your link.');
      } else {
        setError('Failed to select slot. Please try again or contact HR.');
      }
      console.error('Error selecting slot:', err);
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    return () => {
      if (dateSwitchTimerRef.current) {
        clearTimeout(dateSwitchTimerRef.current);
      }
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading available slots...</p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Slot Selected Successfully!</h2>
          <p className="text-gray-600 mb-4">
            Your interview slot has been confirmed. You will receive a confirmation email shortly with all the details.
          </p>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800 font-medium">
              Selected: {selectedSlot?.display || `${selectedSlot?.date} ${selectedSlot?.time}`}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-center mb-8">
            <CalendarDaysIcon className="h-12 w-12 text-blue-600 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-gray-900 mb-2">Select Interview Slot</h1>
            <p className="text-gray-600">Please choose your preferred date and time for the interview</p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {slots.length === 0 ? (
            <div className="text-center py-8">
              <ClockIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">No available slots found.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* Left: Calendar with highlighted slot dates */}
                <div className="md:col-span-1">
                  <div className="flex items-center justify-between mb-3">
                    <button onClick={gotoPrevMonth} className="p-2 rounded-md text-emerald-700 hover:bg-emerald-50" aria-label="Previous month">
                      <ChevronLeftIcon className="h-5 w-5" />
                    </button>
                    <h3 className="text-sm font-semibold text-gray-800">
                      {viewMonth !== null && viewYear !== null ? `${monthNames[viewMonth]} ${viewYear}` : 'Calendar'}
                    </h3>
                    <button onClick={gotoNextMonth} className="p-2 rounded-md text-emerald-700 hover:bg-emerald-50" aria-label="Next month">
                      <ChevronRightIcon className="h-5 w-5" />
                    </button>
                  </div>

                  <div className="grid grid-cols-7 gap-1 mb-1">
                    {weekdayShort.map((w) => (
                      <div key={w} className="text-xs font-medium text-gray-500 text-center py-1">{w}</div>
                    ))}
                  </div>

                  <div className="grid grid-cols-7 gap-1">
                    {getCalendarGrid(viewYear, viewMonth).map(({ date, inMonth, dateStr }, idx) => {
                      const isAvailable = availableDateSet.has(dateStr);
                      const isSelected = selectedDate === dateStr;
                      const base = 'p-2 text-center rounded-lg border text-sm';
                      let styles = inMonth ? 'border-gray-200 bg-white text-gray-700' : 'border-gray-100 bg-white text-gray-300';
                      if (inMonth && isAvailable) {
                        styles = isSelected
                          ? 'bg-emerald-200 border-emerald-500 text-emerald-900 ring-2 ring-emerald-400'
                          : 'bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100 ring-1 ring-emerald-200 cursor-pointer';
                      }
                      return (
                        <button
                          key={`${dateStr}-${idx}`}
                          onClick={() => (inMonth && isAvailable ? handleDateSelect(dateStr) : null)}
                          disabled={!inMonth || !isAvailable}
                          className={`${base} ${styles}`}
                          aria-label={dateStr}
                        >
                          {date.getDate()}
                        </button>
                      );
                    })}
                  </div>

                  <div className="mt-3 text-xs text-gray-500">
                    <div className="flex items-center space-x-2">
                      <span className="inline-block h-3 w-3 rounded-sm bg-emerald-200 border border-emerald-500"></span>
                      <span>Selected date</span>
                    </div>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="inline-block h-3 w-3 rounded-sm bg-emerald-50 border border-emerald-300"></span>
                      <span>Available date</span>
                    </div>
                  </div>
                </div>

                {/* Right: Time slots for selected date */}
                <div className="md:col-span-2">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Available Times</h3>
                  {timesLoading ? (
                    <div className="flex items-center justify-center py-6">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    </div>
                  ) : slots.filter((s) => normalizeDateStr(s.date) === selectedDate).length === 0 ? (
                     <div className="text-gray-600 text-sm">No time slots for this date.</div>
                   ) : (
                     <>
                       <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                         {slots
                           .filter((s) => normalizeDateStr(s.date) === selectedDate)
                           .map((slot, index) => (
                             <button
                               key={`${slot.date}-${slot.time}-${index}`}
                               onClick={() => handleSlotSelect(slot)}
                               className={`p-3 border rounded-lg transition-all flex items-center justify-center ${
                                 selectedSlot?.date === slot.date && selectedSlot?.time === slot.time
                                   ? 'border-emerald-500 bg-emerald-50 ring-2 ring-emerald-200'
                                   : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                               }`}
                             >
                               <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
                               <span className="font-medium text-gray-900">{slot.time}</span>
                             </button>
                           ))}
                       </div>
 
                       {selectedSlot && (
                         <div className="mt-4">
                           <div className="inline-flex items-center gap-2 px-3 py-2 rounded-md border border-blue-200 bg-blue-50 text-blue-800 text-sm">
                             <CheckCircleIcon className="h-4 w-4 text-blue-600" />
                             <div className="flex flex-col">
                               <span className="font-medium">
                                 Selected: {selectedSlot.display || `${selectedSlot.date} ${selectedSlot.time}`}
                               </span>
                               <span className="text-blue-600">Duration: 1 hour</span>
                             </div>
                           </div>
                         </div>
                       )}
                     </>
                   )}
                </div>
              </div>

             
              <div className="flex justify-center">
                <button
                  onClick={handleSubmit}
                  disabled={!selectedSlot || submitting}
                  className={`px-8 py-3 rounded-lg font-medium ${
                    selectedSlot && !submitting
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {submitting ? 'Confirming...' : 'Confirm Selection'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SlotSelection;
