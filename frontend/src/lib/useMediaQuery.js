/**
 * useMediaQuery — minimal hook for responsive layouts.
 *
 * Used as: const isMobile = useMediaQuery('(max-width: 720px)')
 *
 * Avoids pulling in a UI library just for this single capability.
 * Subscribes / unsubscribes correctly with the modern addEventListener
 * API and falls back to addListener for old browsers (kept for
 * defensive completeness; React 18 + modern browsers don't need it).
 */

import { useEffect, useState } from 'react'

export default function useMediaQuery(query) {
  const get = () => typeof window !== 'undefined' && window.matchMedia(query).matches
  const [matches, setMatches] = useState(get)

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mql = window.matchMedia(query)
    const handler = (e) => setMatches(e.matches)
    if (mql.addEventListener) mql.addEventListener('change', handler)
    else mql.addListener(handler)
    setMatches(mql.matches)
    return () => {
      if (mql.removeEventListener) mql.removeEventListener('change', handler)
      else mql.removeListener(handler)
    }
  }, [query])

  return matches
}
