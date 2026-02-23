import { NextRequest, NextResponse } from 'next/server'

// ---------------------------------------------------------------------------
// In-memory sliding-window rate limiter
// ---------------------------------------------------------------------------
// Good enough for internal OEDE use with few concurrent users.
//
// Known limitation on Vercel serverless: state is lost on cold starts and is
// NOT shared across instances.  For production scale, swap this module for
// @upstash/ratelimit + Redis — the API surface is the same so no route
// changes are needed.
// ---------------------------------------------------------------------------

export type RateLimitTier = 'public' | 'authenticated' | 'admin'

interface TierConfig {
  windowMs: number
  maxRequests: number
}

const TIER_CONFIG: Record<RateLimitTier, TierConfig> = {
  public:        { windowMs: 60_000, maxRequests: 30 },
  authenticated: { windowMs: 60_000, maxRequests: 60 },
  admin:         { windowMs: 60_000, maxRequests: 120 },
}

// Each key maps to a list of request timestamps (epoch ms) within the window.
const store = new Map<string, number[]>()

// Auto-cleanup every 5 minutes to prevent unbounded memory growth.
const CLEANUP_INTERVAL_MS = 5 * 60_000

let cleanupTimer: ReturnType<typeof setInterval> | null = null

function ensureCleanup() {
  if (cleanupTimer) return
  cleanupTimer = setInterval(() => {
    const now = Date.now()
    for (const [key, timestamps] of store) {
      // Remove entries whose entire window has expired (use largest window: 60s)
      const filtered = timestamps.filter(t => now - t < 60_000)
      if (filtered.length === 0) {
        store.delete(key)
      } else {
        store.set(key, filtered)
      }
    }
  }, CLEANUP_INTERVAL_MS)
  // Don't block Node from exiting
  if (cleanupTimer && typeof cleanupTimer === 'object' && 'unref' in cleanupTimer) {
    cleanupTimer.unref()
  }
}

export interface RateLimitResult {
  success: boolean
  limit: number
  remaining: number
  reset: number // epoch ms when the window resets
}

/**
 * Check rate limit for a given key and tier.
 *
 * @param key  - Unique identifier (IP or userId)
 * @param tier - One of 'public' | 'authenticated' | 'admin'
 */
export function rateLimit(key: string, tier: RateLimitTier): RateLimitResult {
  ensureCleanup()

  const { windowMs, maxRequests } = TIER_CONFIG[tier]
  const now = Date.now()
  const windowStart = now - windowMs

  const timestamps = (store.get(key) ?? []).filter(t => t > windowStart)

  const success = timestamps.length < maxRequests
  if (success) {
    timestamps.push(now)
  }

  store.set(key, timestamps)

  const oldestInWindow = timestamps[0] ?? now
  const reset = oldestInWindow + windowMs

  return {
    success,
    limit: maxRequests,
    remaining: Math.max(0, maxRequests - timestamps.length),
    reset,
  }
}

/**
 * Build a 429 response with standard rate-limit headers.
 */
export function rateLimitResponse(result: RateLimitResult): NextResponse {
  return NextResponse.json(
    { error: 'Too many requests' },
    {
      status: 429,
      headers: {
        'X-RateLimit-Limit':     String(result.limit),
        'X-RateLimit-Remaining': String(result.remaining),
        'X-RateLimit-Reset':     String(result.reset),
        'Retry-After':           String(Math.ceil((result.reset - Date.now()) / 1000)),
      },
    },
  )
}

/**
 * Extract client IP from request headers (Vercel / reverse-proxy aware).
 */
export function getClientIp(request: NextRequest): string {
  return (
    request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ||
    request.headers.get('x-real-ip') ||
    '127.0.0.1'
  )
}

// ---------------------------------------------------------------------------
// Test helpers — only exported so unit tests can reset state between runs.
// ---------------------------------------------------------------------------
export function _resetStore() {
  store.clear()
}
