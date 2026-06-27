import { useEffect, useRef } from 'react'

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function useFocusTrap(active: boolean) {
  const ref = useRef<HTMLDivElement>(null)
  const prev = useRef<Element | null>(null)

  useEffect(() => {
    if (!active) return
    prev.current = document.activeElement

    const el = ref.current
    if (!el) return

    const focusable = el.querySelectorAll<HTMLElement>(FOCUSABLE)
    const first = focusable[0]

    first?.focus()

    const handler = (e: KeyboardEvent) => {
      if (e.key !== 'Tab' || !el.contains(document.activeElement)) return
      const focusable = el.querySelectorAll<HTMLElement>(FOCUSABLE)
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault(); last?.focus()
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault(); first?.focus()
      }
    }

    document.addEventListener('keydown', handler)
    return () => {
      document.removeEventListener('keydown', handler)
      ;(prev.current as HTMLElement)?.focus()
    }
  }, [active])

  return ref
}
