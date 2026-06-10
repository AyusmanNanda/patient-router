import { useState } from 'react'
import api from '../api/api'

import type {
    DataStatsResponse,
    GenerateDataResponse
} from '../types/dataTypes'

interface ApiError {
    response?: {
        data?: {
            error?: string
        }
    }
}

export function useDataManager() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const [stats, setStats] =
        useState<DataStatsResponse | null>(null)

    const [generateResult, setGenerateResult] =
        useState<GenerateDataResponse | null>(null)

    const loadStats = async () => {
        setLoading(true)
        setError('')

        try {
            const { data } =
                await api.get<DataStatsResponse>('/data')

            setStats(data)

        } catch (e: unknown) {
            const err = e as ApiError

            if (err.response?.data?.error) {
                setError(err.response.data.error)
            } else if (e instanceof Error) {
                setError(e.message)
            } else {
                setError('Failed to load dataset statistics.')
            }
        } finally {
            setLoading(false)
        }
    }

    const generateDataset = async (
        rows: number
    ) => {
        setLoading(true)
        setError('')

        try {
            const { data } =
                await api.post<GenerateDataResponse>(
                    '/data/generate',
                    { rows }
                )

            setGenerateResult(data)

            await loadStats()

        } catch (e: unknown) {
            const err = e as ApiError

            if (err.response?.data?.error) {
                setError(err.response.data.error)
            } else if (e instanceof Error) {
                setError(e.message)
            } else {
                setError('Failed to generate dataset.')
            }
        } finally {
            setLoading(false)
        }
    }

    return {
        loading,
        error,

        stats,
        generateResult,

        loadStats,
        generateDataset,
    }
}