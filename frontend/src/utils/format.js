/**
 * Bulletproof data-formatting helpers.
 *
 * Every helper is defensive: it accepts ANY input (null, undefined, "",
 * NaN, objects, arrays) and always returns a safe, displayable value.
 * UI code should never call `.toFixed`, `.toLocaleString`, or `parseFloat`
 * directly on API data — route it through here instead.
 */

/** Coerce anything into a finite number, falling back to `fallback` (default 0). */
export function toNumber(value, fallback = 0) {
  if (typeof value === 'number') return Number.isFinite(value) ? value : fallback;
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

/** Format a value as INR-style currency, e.g. "Rs 1,234.50". Never throws. */
export function money(value, fallback = 0) {
  const n = toNumber(value, fallback);
  return `Rs ${n.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/** Format an integer with thousands separators, e.g. "1,234". Never throws. */
export function integer(value, fallback = 0) {
  const n = Math.round(toNumber(value, fallback));
  return n.toLocaleString();
}

/** Fixed-decimal string, e.g. "12.50". Never throws. */
export function decimal(value, digits = 2, fallback = 0) {
  return toNumber(value, fallback).toFixed(digits);
}

/** Safe string: trims, returns `fallback` for null/undefined/empty. */
export function text(value, fallback = '—') {
  if (value === null || value === undefined) return fallback;
  const str = String(value).trim();
  return str.length ? str : fallback;
}

/** Always return an array; non-arrays (including null/undefined) become []. */
export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

/**
 * Format an ISO date (e.g. "2026-06-01") as "01 Jun 2026". Never throws;
 * returns `fallback` for anything unparseable.
 */
export function dateLabel(value, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return text(value, fallback);
  return parsed.toLocaleDateString(undefined, {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

/**
 * Extract a human-readable message from an Axios/API error.
 * FastAPI returns `detail` as either a string OR an array of validation
 * objects ({ msg, loc, ... }); rendering the array directly crashes React,
 * so we always flatten it to a string.
 */
export function getErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) {
    const msg = detail
      .map((item) => (typeof item === 'string' ? item : item?.msg))
      .filter(Boolean)
      .join(' ');
    return msg || fallback;
  }
  if (typeof detail === 'string' && detail.trim()) return detail;
  if (typeof error?.message === 'string' && error.message.trim()) return error.message;
  return fallback;
}
