import { useCallback, useEffect, useState } from 'react'
import api from '../api/api'
import type { LogsResponse } from '../types/logsTypes'

export function useLogs() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [data, setData] =
        useState<LogsResponse | null>(null)

    const loadLogs = useCallback(async () => {
        setLoading(true)
        setError('')

        try {
            const response =
                await api.get<LogsResponse>('/logs')

            setData(response.data)

        } catch (e) {
            if (e instanceof Error) {
                setError(e.message)
            } else {
                setError('Failed to load logs.')
            }
        } finally {
            setLoading(false)
        }
    }, [])

    const clearLogs = async () => {
        await api.post('/logs/clear')
        await loadLogs()
    }

    useEffect(() => {
        void loadLogs()
    }, [loadLogs])

    return {
        loading,
        error,
        data,
        clearLogs,
        reload: loadLogs,
    }
}