// Copyright (c) 2026 Blueway Consulting LLC.
// Licensed under the LGPL-3.0 License. See LICENSE file for details.

export const isValidTimeFormat = (timeStr) => {
  // Accepts "YYYY-MM-DD HH:mm:ss" or "DD-MM-YYYY HH:mm:ss"
  const isoRegex = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/;
  const altRegex = /^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}$/;
  return isoRegex.test(timeStr) || altRegex.test(timeStr);
}

export const validateTimeLogs = (timeLogs) => {
  const errors = [];

  timeLogs.forEach((log, index) => {
    if (!isValidTimeFormat(log.from_time)) {
      errors.push(`Log ${index + 1}: Invalid from_time format → ${log.from_time}`);
    }
    if (!isValidTimeFormat(log.to_time)) {
      errors.push(`Log ${index + 1}: Invalid to_time format → ${log.to_time}`);
    }
  });

  return errors;
}