import { useEffect, useState } from 'react'
import { isTabletDevice } from '../utils/isTabletDevice'
import { computeShellMaxClass } from '../utils/shellMax'

export function useShellMaxClass(): string {
  const [maxClass, setMaxClass] = useState(() =>
    computeShellMaxClass(typeof window === 'undefined' ? 0 : window.innerWidth, isTabletDevice()),
  )

  useEffect(() => {
    const tablet = isTabletDevice()
    const update = () => setMaxClass(computeShellMaxClass(window.innerWidth, tablet))
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  return maxClass
}
