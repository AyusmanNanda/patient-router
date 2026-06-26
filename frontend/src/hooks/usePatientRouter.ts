import { useState } from 'react'
import api from '../api/api'
import type { PredictResponse, PredictRequest, FeedbackRequest } from '../types/prediction'

export function usePatientRouter() {
    const [symptoms,  setSymptoms]  = useState<string[]>([])
    const [vitals,    setVitals]    = useState<string[]>([])
    const [age,       setAge]       = useState('')
    const [duration,  setDuration]  = useState('')
    const [gender,    setGender]    = useState('male')
    const [history, setHistory] = useState<string[]>([])
    const [loading,   setLoading]   = useState(false)
    const [error,     setError]     = useState('')
    const [result,    setResult]    = useState<PredictResponse | null>(null)

    const [fbState,     setFbState]     = useState<'idle' | 'correction'>('idle')
    const [correctDept, setCorrectDept] = useState('cardiology')
    const [fbDone,      setFbDone]      = useState(false)

    const reset = () => {
        setSymptoms([]); setVitals([]); setAge(''); setDuration('')
        setGender('male'); setError(''); setResult(null)
        setHistory([])
        setFbState('idle'); setFbDone(false)
    }

    const predict = async () => {
        setError('')

        if (!symptoms.length) return setError('At least one symptom is required.')
        const a = Number(age)
        if (!a || a <= 0 || a > 120) return setError('Please enter a valid age (1–120).')
        const d = Number(duration)
        if (!d || d <= 0) return setError('Please enter a valid symptom duration.')

        setLoading(true)
        setResult(null)
        setFbState('idle')
        setFbDone(false)

        try {
            const payload: PredictRequest = {
                symptoms: symptoms.join(', '),
                vitals:   vitals.join(', '),
                age:      a,
                duration: d,
                gender,
                history: history.join(', '),
            }

            const { data } = await api.post<PredictResponse>('/predict', payload)
            setResult(data)

        } catch (e: unknown) {
            if (
                e &&
                typeof e === 'object' &&
                'response' in e &&
                (e as { response?: { data?: { error?: string } } }).response?.data?.error
            ) {
                setError((e as { response: { data: { error: string } } }).response.data.error)
            } else if (e instanceof Error) {
                setError(e.message)
            } else {
                setError('Unexpected error. Is the Flask server running?')
            }
        } finally {
            setLoading(false)
        }
    }

    const submitFeedback = async (correct: boolean) => {
        if (correct) {
            setFbDone(true)
            return
        }
        if (fbState !== 'correction') {
            setFbState('correction')
            return
        }
        const payload: FeedbackRequest = {
            symptoms: symptoms.join(', '),
            vitals:   vitals.join(', '),
            gender,
            age:      Number(age),
            duration: Number(duration),
            priority: result?.priority ?? 'low',
            correct_department: correctDept,
        }

        await api.post('/feedback', payload).catch(() => null)
        setFbDone(true)
    }

    const priorityClass = result ? `priority-${result.priority}` : ''


    return{
        symptoms,
        setSymptoms,
        vitals,
        setVitals,
        age,
        setAge,
        duration,
        setDuration,
        gender,
        setGender,
        loading,
        setLoading,
        error,
        setError,
        result,
        setResult,
        fbState,
        setFbState,
        correctDept,
        setCorrectDept,
        fbDone,
        setFbDone,
        reset,
        predict,
        submitFeedback,
        priorityClass,
        history,
        setHistory,
    }
}
