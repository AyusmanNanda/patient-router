import { useCallback, useEffect, useState } from 'react'
import api from '../api/api'

export function useBackendStatus() {
    const [isOffline, setIsOffline] = useState(false)
    const [checking, setChecking] = useState(true)

    const checkConnection = useCallback(async () => {
        setChecking(true)

        try {
            await api.get('/health')
            setIsOffline(false)
        } catch {
            setIsOffline(true)
        } finally {
            setChecking(false)
        }
    }, [])

    useEffect(() => {
        void checkConnection()

        const handleOnline = () => {
            void checkConnection()
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
    }, [checkConnection])

    return {
        isOffline,
        checking,
        checkConnection,
    }
}