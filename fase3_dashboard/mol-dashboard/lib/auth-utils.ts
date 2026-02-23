/**
 * Allowed redirect paths after authentication.
 * Only paths starting with these prefixes are accepted.
 * This prevents open redirect attacks (S-02).
 */
export const ALLOWED_REDIRECT_PATHS = [
  '/home',
  '/dashboard',
  '/admin',
  '/cuenta',
  '/skills',
  '/informes',
  '/checkout',
  '/precios',
]

/**
 * Validates a redirect path against the whitelist.
 * Rejects absolute URLs, protocol-relative URLs, and unknown paths.
 */
export function isAllowedRedirectPath(path: string | null | undefined): boolean {
  if (!path || typeof path !== 'string' || !path.trim()) return false

  const trimmed = path.trim()

  // Reject absolute URLs (http://, https://, //, javascript:, etc.)
  if (/^[a-zA-Z][a-zA-Z\d+\-.]*:/.test(trimmed)) return false
  if (trimmed.startsWith('//')) return false
  if (trimmed.startsWith('/\\')) return false

  // Must start with /
  if (!trimmed.startsWith('/')) return false

  // Check against whitelist
  return ALLOWED_REDIRECT_PATHS.some((allowed) => trimmed.startsWith(allowed))
}

/**
 * Returns a safe redirect path, falling back to /home if invalid.
 */
export function getSafeRedirectPath(next: string | null | undefined): string {
  return isAllowedRedirectPath(next) ? next!.trim() : '/home'
}
