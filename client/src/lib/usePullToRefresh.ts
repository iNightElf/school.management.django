import { useEffect } from 'react'

export function usePullToRefresh() {
  useEffect(() => {
    let startY = 0
    let active = false

    const onTouchStart = (e: TouchEvent) => {
      if (window.scrollY > 0) return
      startY = e.touches[0].clientY
      active = true
    }

    const onTouchMove = (e: TouchEvent) => {
      if (!active || window.scrollY > 0) return
      const dy = e.touches[0].clientY - startY
      if (dy > 60) {
        window.location.reload()
        active = false
      }
    }

    const onTouchEnd = () => { active = false }

    window.addEventListener('touchstart', onTouchStart, { passive: true })
    window.addEventListener('touchmove', onTouchMove, { passive: true })
    window.addEventListener('touchend', onTouchEnd)
    return () => {
      window.removeEventListener('touchstart', onTouchStart)
      window.removeEventListener('touchmove', onTouchMove)
      window.removeEventListener('touchend', onTouchEnd)
    }
  }, [])
}
