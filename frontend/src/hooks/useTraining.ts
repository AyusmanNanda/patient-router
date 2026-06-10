import { useState } from 'react'
import api from '../api/api'
import type { TrainingResponse } from '../types/trainingTypes'

interface ApiError {
    response?: {
        data?: {
            error?: string
        }
    }
}

type TrainingStatus =
    | 'idle'
    | 'training'
    | 'success'
    | 'error'

export function useTraining() {
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState('')
    const [status, setStatus] =
        useState<TrainingStatus>('idle')

    const [result, setResult] =
        useState<TrainingResponse | null>(null)

    const train = async () => {
        setLoading(true)
        setStatus('training')
        setError('')
        setResult(null)

        try {
            const { data } =
                await api.post<TrainingResponse>('/train')

            setResult(data)
            setStatus('success')

        } catch (e: unknown) {
            const err = e as ApiError

            if (err.response?.data?.error) {
                setError(err.response.data.error)
            } else if (e instanceof Error) {
                setError(e.message)
            } else {
                setError('Failed to train model.')
            }

            setStatus('error')
        } finally {
            setLoading(false)
        }
    }

    return {
        loading,
        error,
        status,
        result,
        train,
    }
}