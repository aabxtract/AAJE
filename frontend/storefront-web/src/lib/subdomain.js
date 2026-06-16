/**
 * Subdomain detection for storefront routing.
 *
 * Buyer URL: `<slug>.aaje.store` (prod) or `<slug>.localtest.me:5174` (dev).
 * Apex URL: `aaje.store`, `localhost`, `127.0.0.1`, `localtest.me`.
 *
 * `localtest.me` resolves to 127.0.0.1 for any subdomain without /etc/hosts
 * edits — so `ada-fashions.localtest.me:5174` Just Works in dev.
 */

const APEX_HOSTS = new Set([
  'aaje.store',
  'www.aaje.store',
  'localhost',
  '127.0.0.1',
  'localtest.me',
  '0.0.0.0',
])

const RESERVED_SUBDOMAINS = new Set([
  'www',
  'app',
  'api',
  'admin',
  'dashboard',
  'staging',
  'preview',
])

/**
 * Returns the storefront slug from the current hostname, or null if we're
 * on the apex (no subdomain) or on a reserved subdomain like `app.aaje.store`.
 */
export function detectStoreSlug(hostname = window.location.hostname) {
  const host = (hostname || '').toLowerCase()
  if (APEX_HOSTS.has(host)) return null
  if (host.endsWith('.aaje.store')) {
    const sub = host.slice(0, -'.aaje.store'.length)
    return RESERVED_SUBDOMAINS.has(sub) ? null : sub || null
  }
  if (host.endsWith('.localtest.me')) {
    const sub = host.slice(0, -'.localtest.me'.length)
    return RESERVED_SUBDOMAINS.has(sub) ? null : sub || null
  }
  return null
}
