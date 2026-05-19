import type { ReactNode } from 'react'

/**
 * Desktop: schmale, zentrierte Auth-Karte (~480px), mehr Abstand oben.
 */
export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-dvh overflow-x-hidden bg-[#09090b] pb-12">
      <div className="mx-auto flex w-full max-w-[480px] flex-col px-4 pt-10 sm:pt-14">
        <div aria-hidden className="mb-2 flex justify-center">
          <div className="h-1 w-12 rounded-full bg-orange-500" />
        </div>
        {children}
      </div>
    </div>
  )
}
