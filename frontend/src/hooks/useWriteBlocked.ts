import { LICENSE_SUSPENDED_MESSAGE } from '../constants/license'
import { useAuth } from '../context/AuthContext'

export function useWriteBlocked() {
  const { licenseActive } = useAuth()
  return {
    writeBlocked: !licenseActive,
    message: LICENSE_SUSPENDED_MESSAGE,
  }
}
