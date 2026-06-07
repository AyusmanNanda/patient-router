import { useState } from 'react'
import { Send, RotateCcw, AlertTriangle, ThumbsUp, ThumbsDown } from 'lucide-react'
import TagInput from '../components/layout/TagInput.tsx'
import Topbar from '../components/layout/Topbar.tsx'
import api from '../api/api'
import type { PredictResponse, PredictRequest, FeedbackRequest } from '../types/prediction'

const SYMPTOMS = [
    'abdominal pain', 'blurred vision', 'body pain', 'breathlessness', 'chest pain',
    'confusion', 'cough', 'diarrhea', 'dizziness', 'fatigue', 'fever', 'headache',
    'joint pain', 'limited movement', 'nausea', 'stiffness', 'sweating', 'swelling',
    'vomiting', 'weakness',
]

const VITALS = ['bp_high', 'bp_low', 'hr_high', 'hr_low', 'temp_high', 'temp_low', 'normal']
const DEPTS  = ['cardiology', 'pulmonology', 'neurology', 'orthopedics', 'gastrology', 'general']

export default function PatientRouter() {
    const [symptoms,  setSymptoms]  = useState<string[]>([])
    const [vitals,    setVitals]    = useState<string[]>([])
    const [age,       setAge]       = useState('')
    const [duration,  setDuration]  = useState('')
    const [gender,    setGender]    = useState('male')
    const [loading,   setLoading]   = useState(false)
    const [error,     setError]     = useState('')
    const [result,    setResult]    = useState<PredictResponse | null>(null)

    // feedback state
    const [fbState,     setFbState]     = useState<'idle' | 'correction'>('idle')
    const [correctDept, setCorrectDept] = useState('cardiology')
    const [fbDone,      setFbDone]      = useState(false)

    const reset = () => {
        setSymptoms([]); setVitals([]); setAge(''); setDuration('')
        setGender('male'); setError(''); setResult(null)
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
            }

            const { data } = await api.post<PredictResponse>('/predict', payload)
            setResult(data)

        } catch (e: unknown) {
            // axios wraps errors — extract message from response if available
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

        // First click "No" → show correction dropdown
        if (fbState !== 'correction') {
            setFbState('correction')
            return
        }

        // Second click → save correction
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

    return (
        <div>
            <Topbar title="Patient Router" subtitle="Enter patient data to get department triage recommendation" />
            <div className="page-body">
                <div className="two-col" style={{ alignItems: 'start' }}>

                    {/* ── Input Form ── */}
                    <div>
                        <div className="card">
                            <div className="card-title">
                                <span>Patient Information</span>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Symptoms <span className="req">*</span></label>
                                <TagInput
                                    options={SYMPTOMS}
                                    value={symptoms}
                                    onChange={setSymptoms}
                                    placeholder="Type to search symptoms…"
                                />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Vital Signs</label>
                                <TagInput
                                    options={VITALS}
                                    value={vitals}
                                    onChange={setVitals}
                                    placeholder="Type to search vitals…"
                                />
                            </div>

                            <div className="form-row" style={{ marginBottom: 18 }}>
                                <div className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">Age <span className="req">*</span></label>
                                    <input
                                        className="form-input"
                                        type="number"
                                        min={0}
                                        max={120}
                                        placeholder="e.g. 45"
                                        value={age}
                                        onChange={e => setAge(e.target.value)}
                                    />
                                </div>
                                <div className="form-group" style={{ marginBottom: 0 }}>
                                    <label className="form-label">Gender</label>
                                    <select className="form-select" value={gender} onChange={e => setGender(e.target.value)}>
                                        <option value="male">Male</option>
                                        <option value="female">Female</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Duration (days) <span className="req">*</span></label>
                                <input
                                    className="form-input"
                                    type="number"
                                    min={0}
                                    placeholder="e.g. 3"
                                    value={duration}
                                    onChange={e => setDuration(e.target.value)}
                                />
                            </div>

                            {error && <div className="error-box">⚠ {error}</div>}

                            <div className="btn-group" style={{ marginTop: 6 }}>
                                <button
                                    className="btn btn-primary btn-lg"
                                    onClick={predict}
                                    disabled={loading}
                                    style={{ flex: 1 }}
                                >
                                    {loading
                                        ? <><span className="spinner" /> Analyzing…</>
                                        : <><Send size={14} /> Predict Department</>
                                    }
                                </button>
                                <button className="btn btn-ghost" onClick={reset}>
                                    <RotateCcw size={14} /> Reset
                                </button>
                            </div>
                        </div>

                        {/* Feedback */}
                        {result && !fbDone && (
                            <div className="card" style={{ marginTop: 16 }}>
                                <div className="card-title">Prediction Feedback</div>
                                <p style={{ fontSize: 13, color: 'var(--slate-600)', marginBottom: 12 }}>
                                    Was this department recommendation accurate?
                                </p>
                                <div className="btn-group">
                                    <button className="btn btn-success" onClick={() => submitFeedback(true)}>
                                        <ThumbsUp size={14} /> Yes, correct
                                    </button>
                                    <button className="btn btn-danger" onClick={() => submitFeedback(false)}>
                                        <ThumbsDown size={14} /> No, incorrect
                                    </button>
                                </div>

                                {fbState === 'correction' && (
                                    <div style={{ marginTop: 16 }}>
                                        <label className="form-label">Correct Department</label>
                                        <select
                                            className="form-select"
                                            style={{ marginBottom: 12 }}
                                            value={correctDept}
                                            onChange={e => setCorrectDept(e.target.value)}
                                        >
                                            {DEPTS.map(d => (
                                                <option key={d} value={d}>
                                                    {d.charAt(0).toUpperCase() + d.slice(1)}
                                                </option>
                                            ))}
                                        </select>
                                        <button className="btn btn-blue" onClick={() => submitFeedback(false)}>
                                            Save Correction to Training Data
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {fbDone && (
                            <div className="card" style={{ marginTop: 16, background: 'var(--green-50)', borderColor: '#86efac' }}>
                                <p style={{ fontSize: 13, color: '#065f46' }}>✓ Feedback recorded. Thank you!</p>
                            </div>
                        )}
                    </div>

                    {/* ── Result ── */}
                    <div>
                        {!result && !loading && (
                            <div className="card" style={{ textAlign: 'center', padding: '48px 24px', borderStyle: 'dashed' }}>
                                <div style={{ fontSize: 36, marginBottom: 12 }}>🏥</div>
                                <div style={{ fontSize: 14, color: 'var(--slate-400)', fontWeight: 500 }}>
                                    Fill in patient details and click<br />
                                    <strong style={{ color: 'var(--slate-600)' }}>Predict Department</strong>
                                </div>
                            </div>
                        )}

                        {result && (
                            <>
                                {/* Priority banner */}
                                <div className={`priority-banner ${priorityClass}`}>
                                    <span className="priority-badge">{result.priority.toUpperCase()}</span>
                                    <div className="priority-text">
                                        <div className="dept-name">
                                            {result.recommended.replace(/_/g, ' ').toUpperCase()}
                                        </div>
                                        <div className="dept-sub">Recommended department</div>
                                    </div>
                                    {result.emergency && (
                                        <span className="emergency-badge">⚠ EMERGENCY</span>
                                    )}
                                </div>

                                {/* Confidence & meta */}
                                <div className="card">
                                    <div className="result-kv">
                                        <span className="rk">ML Confidence</span>
                                        <span className="rv">{(result.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="result-kv">
                                        <span className="rk">Model Version</span>
                                        <span className="rv">{result.model_version}</span>
                                    </div>
                                    <div className="result-kv">
                                        <span className="rk">Priority Level</span>
                                        <span className="rv">{result.priority}</span>
                                    </div>
                                </div>

                                {/* Department ranking */}
                                <div className="card" style={{ marginTop: 14 }}>
                                    <div className="card-title">Department Ranking</div>
                                    <div className="dept-list">
                                        {result.departments.map((d, i) => (
                                            <div className="dept-row" key={d.department}>
                                                <span className="dept-rank">#{i + 1}</span>
                                                <span className="dept-name-text">{d.department.replace(/_/g, ' ')}</span>
                                                <div className="dept-bar-wrap">
                                                    <div
                                                        className="dept-bar-fill"
                                                        style={{ width: `${(d.confidence * 100).toFixed(0)}%` }}
                                                    />
                                                </div>
                                                <span className="dept-pct">{(d.confidence * 100).toFixed(1)}%</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {/* Clinical reasoning */}
                                {result.reasons?.length > 0 && (
                                    <div className="card" style={{ marginTop: 14 }}>
                                        <div className="card-title">Clinical Reasoning</div>
                                        <ul className="reasons-ul">
                                            {result.reasons.map((r, i) => <li key={i}>{r}</li>)}
                                        </ul>
                                    </div>
                                )}

                                {/* Warning */}
                                {result.warning && (
                                    <div className="warning-box" style={{ marginTop: 14 }}>
                                        <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                                        <span style={{ fontSize: 13 }}>{result.warning}</span>
                                    </div>
                                )}

                                {/* Raw JSON */}
                                <details>
                                    <summary>View raw API response</summary>
                                    <pre className="raw-json">{JSON.stringify(result, null, 2)}</pre>
                                </details>
                            </>
                        )}
                    </div>
                </div>
            </div>
        </div>
    )
}