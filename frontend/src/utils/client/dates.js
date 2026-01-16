// Calculate start and end dates for the current week
export function getWeekDates(date = new Date()) {
    // Create a new date object to avoid modifying the original
    const inputDate = new Date(date);

    // Get the day of the week (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
    const dayOfWeek = inputDate.getDay();

    // Calculate start date (Sunday)
    const startDate = new Date(inputDate);
    startDate.setDate(inputDate.getDate() - dayOfWeek);

    // Calculate end date (Saturday)
    const endDate = new Date(inputDate);
    endDate.setDate(inputDate.getDate() + (6 - dayOfWeek));

    // Set startDate to 00:00:00
    startDate.setHours(0, 0, 0, 0);

    // Set endDate to 23:59:59
    endDate.setHours(23, 59, 59, 999);

    return {
        start: getFormattedISODate(startDate), // UTC ISO string for Sunday at 00:00:00
        end: getFormattedISODate(endDate) // UTC ISO string for Saturday at 23:59:59
    };
}

export function getMonthRangeDates(date = new Date()) {
  // Clone the input date to avoid mutating the original
  const endDate = new Date(date);
  const startDate = new Date(date);
  startDate.setDate(endDate.getDate() - 29); // 30 days total including today

  // Set startDate to 00:00:00
  startDate.setHours(0, 0, 0, 0);

  // Set endDate to 23:59:59
  endDate.setHours(23, 59, 59, 999);

  return {
    start: getFormattedISODate(startDate), // UTC ISO string for 30 days ago at 00:00:00
    end: getFormattedISODate(endDate)      // UTC ISO string for today at 23:59:59
  };
}

// Calculate start and end (full month) for the month containing the given date
export function getMonthBoundaryDates(date = new Date()) {
  const startDate = new Date(date.getFullYear(), date.getMonth(), 1)
  const endDate = new Date(date.getFullYear(), date.getMonth() + 1, 0)

  startDate.setHours(0, 0, 0, 0)
  endDate.setHours(23, 59, 59, 999)

  return {
    start: getFormattedISODate(startDate),
    end: getFormattedISODate(endDate)
  }
}

// Calculate start and end (00:00:00 to 23:59:59) for a single day
export function getDayRangeDates(date = new Date()) {
  const startDate = new Date(date);
  const endDate = new Date(date);

  // Start of day (local), end of day (local)
  startDate.setHours(0, 0, 0, 0);
  endDate.setHours(23, 59, 59, 999);

  return {
    start: getFormattedISODate(startDate), // UTC ISO string for local 00:00:00
    end: getFormattedISODate(endDate)      // UTC ISO string for local 23:59:59
  };
}

// Helper function to format time for display
export function formatTime(date) {
    if (!(date instanceof Date)) return "";
    return date.toTimeString().substring(0, 5); // HH:MM format
}

/**
 * Formats a date object into an ISO 8601 UTC string (e.g., 2025-08-29T14:30:00+00:00).
 * Always returns time in UTC with a '+00:00' offset, regardless of the local timezone.
 * @param {Date} date
 * @returns {string}
 */
export function getFormattedISODate(date) {
  const year = date.getUTCFullYear();
  const month = (date.getUTCMonth() + 1).toString().padStart(2, '0');
  const day = date.getUTCDate().toString().padStart(2, '0');
  const hours = date.getUTCHours().toString().padStart(2, '0');
  const minutes = date.getUTCMinutes().toString().padStart(2, '0');
  const seconds = date.getUTCSeconds().toString().padStart(2, '0');

  // Always UTC offset in +/-HH:MM format
  const offset = '+00:00';
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}${offset}`;
}

/**
 * Parses an ISO 8601 string with timezone (e.g., "2025-08-29T14:30:00+00:00")
 * and returns a Date representing that exact instant in time. Using local
 * getters (e.g., getHours) or toString() will reflect the local timezone.
 * Returns null if the input is invalid.
 *
 * This is the inverse of getFormattedISODate.
 * @param {string} isoString
 * @returns {Date|null}
 */
export function parseISOToLocalDate(isoString) {
  if (typeof isoString !== 'string') return null;

  // First attempt: rely on native ISO 8601 parsing (handles timezone offsets)
  let d = new Date(isoString);
  if (!Number.isNaN(d.getTime())) return d;

  // Fallback: normalize timezone offset by removing the colon in "+HH:MM" -> "+HHMM"
  // Some older engines can be picky about the colon in the offset.
  const normalized = isoString.replace(/([+-]\d{2}):?(\d{2})$/, '$1$2');
  d = new Date(normalized);
  return Number.isNaN(d.getTime()) ? null : d;
}

/**
 * Calculates hours, minutes, and seconds from a decimal hours value.
 * For example: 1.5 hours = 1 hour, 30 minutes, 0 seconds
 * @param {number} decimalHours - The decimal hours value (e.g., 1.5, 2.25)
 * @returns {Object} An object with hours, minutes, and seconds as integers
 */
export function calculateTimeComponents(decimalHours) {
  const totalSeconds = decimalHours * 3600
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = Math.floor(totalSeconds % 60)

  return { hours, minutes, seconds }
}

/**
 * Updates the time range for a time log and cascades changes to all subsequent logs.
 * When a log's hours are modified, this function:
 * 1. Updates the modified log's from_time and to_time
 * 2. Cascades the change to all subsequent logs, maintaining the time sequence
 *
 * @param {Array} timeLogs - Array of time log objects
 * @param {Object} log - The time log being modified
 * @param {number} index - Index of the log in the timeLogs array
 */
export function updateTimeLogRanges(timeLogs, log, index) {
  // For the first log, use its existing from_time
  // For subsequent logs, use the previous log's to_time
  const fromTime = index === 0
    ? log.from_time
    : timeLogs[index - 1].to_time

  const toTime = new Date(fromTime)
  const { hours, minutes, seconds } = calculateTimeComponents(log.hours)

  toTime.setHours(toTime.getHours() + hours)
  toTime.setMinutes(toTime.getMinutes() + minutes)
  toTime.setSeconds(toTime.getSeconds() + seconds)

  const year = toTime.getFullYear()
  const month = String(toTime.getMonth() + 1).padStart(2, '0')
  const day = String(toTime.getDate()).padStart(2, '0')
  const hoursStr = String(toTime.getHours()).padStart(2, '0')
  const minutesStr = String(toTime.getMinutes()).padStart(2, '0')
  const secondsStr = String(toTime.getSeconds()).padStart(2, '0')

  log.from_time = fromTime
  log.to_time = `${year}-${month}-${day} ${hoursStr}:${minutesStr}:${secondsStr}`

  // Cascade the change to all subsequent time_logs
  for (let i = index + 1; i < timeLogs.length; i++) {
    const currentLog = timeLogs[i]
    const previousLog = timeLogs[i - 1]

    // Set from_time to previous log's to_time
    currentLog.from_time = previousLog.to_time

    // Calculate new to_time based on current log's hours
    const currentToTime = new Date(currentLog.from_time)
    const { hours: h, minutes: m, seconds: s } = calculateTimeComponents(currentLog.hours)

    currentToTime.setHours(currentToTime.getHours() + h)
    currentToTime.setMinutes(currentToTime.getMinutes() + m)
    currentToTime.setSeconds(currentToTime.getSeconds() + s)

    const y = currentToTime.getFullYear()
    const mo = String(currentToTime.getMonth() + 1).padStart(2, '0')
    const d = String(currentToTime.getDate()).padStart(2, '0')
    const hr = String(currentToTime.getHours()).padStart(2, '0')
    const min = String(currentToTime.getMinutes()).padStart(2, '0')
    const sec = String(currentToTime.getSeconds()).padStart(2, '0')

    currentLog.to_time = `${y}-${mo}-${d} ${hr}:${min}:${sec}`
  }
}
