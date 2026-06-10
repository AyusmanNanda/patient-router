import { useState } from 'react'
import api from '../api/api'
import type { EvaluationResponse } from '../types/evaluationType'

interface ApiError {
    response?: {
        data?: {
            error?: string
        }
    }
}

export function useEvaluation() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')

    const [result, setResult] =
        useState<EvaluationResponse | null>(null)

    const loadEvaluation = async () => {
        setLoading(true)
        setError('')

        try {
            const { data } =
                await api.get<EvaluationResponse>(
                    '/evaluation'
                )

            setResult(data)

        } catch (e: unknown) {
            const err = e as ApiError

            if (err.response?.data?.error) {
                setError(err.response.data.error)
            } else if (e instanceof Error) {
                setError(e.message)
            } else {
                setError('Failed to load evaluation.')
            }
        } finally {
            setLoading(false)
        }
    }

    return {
        loading,
        error,
        result,
        loadEvaluation,
    }
}