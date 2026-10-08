/**
 * App-Schale: Handy bleibt 390px, Tablet 720px (UA, unverändert).
 * Büro-PC/Laptop nur über Fensterbreite — nicht per User-Agent.
 * Schwelle 1024px, damit Handy-Querformat nicht zum Büro-Layout wird.
 */
export const DESKTOP_LAYOUT_MIN_PX = 1024

export const SHELL_MAX_PHONE = 'max-w-[390px]'
export const SHELL_MAX_TABLET = 'max-w-[720px]'
export const SHELL_MAX_DESKTOP = 'max-w-[960px]'

export function computeShellMaxClass(viewportWidth: number, isTablet: boolean): string {
  if (isTablet) return SHELL_MAX_TABLET
  if (viewportWidth >= DESKTOP_LAYOUT_MIN_PX) return SHELL_MAX_DESKTOP
  return SHELL_MAX_PHONE
}
