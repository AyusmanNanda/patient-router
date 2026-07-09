import { useCallback, useEffect, useState } from 'react'

export function useBackendStatus() {
    const [isOffline, setIsOffline] = useState(() => !navigator.onLine)

    const checkConnection = useCallback(() => {
        setIsOffline(!navigator.onLine)
    }, [])

    useEffect(() => {
        const handleOnline = () => {
            setIsOffline(false)
        }

        const handleOffline = () => {
            setIsOffline(true)
        }

        window.addEventListener('online', handleOnline)
        window.addEventListener('offline', handleOffline)

        return () => {
            window.removeEventListener('online', handleOnline)
            window.removeEventListener('offline', handleOffline)
        }
    }, [])

    return {
        isOffline,
        checking: false,
        checkConnection,
    }
}