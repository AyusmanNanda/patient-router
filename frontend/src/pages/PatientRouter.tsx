import { AlertTriangle, ThumbsUp, ThumbsDown } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { usePatientRouter } from "../hooks/usePatientRouter.ts";
import { DEPTS } from "../constants/patientOptions.ts";
import PatientForm from "../components/patient-router/patientForm";

export default function PatientRouter() {
    const router = usePatientRouter();
    return (
        <div>
            <Topbar
                title="Patient Router"
                subtitle="Enter patient data to get department triage recommendation"
            />

            <div className="page-body">

                <div className="card" style={{ marginBottom: 16 }}>
                    <label className="form-label">Prediction Engine</label>

                    <select
                        className="form-select"
                        value={router.method}
                        onChange={(e) =>
                            router.setMethod(
                                e.target.value as "patient_router" | "llm" | "hybrid"
                            )
                        }
                    >
                        <option value="patient_router">Patient Router (Local ML)</option>
                        <option value="llm">Gemini 2.5 Flash (LLM)</option>
                        <option value="hybrid">Patient Router + Gemini 2.5 Flash (Hybrid)</option>
                    </select>
                </div>

                <div className="two-col" style={{ alignItems: "start" }}>
                    <div>
                        <PatientForm
                            symptoms={router.symptoms}
                            setSymptoms={router.setSymptoms}
                            vitals={router.vitals}
                            setVitals={router.setVitals}
                            age={router.age}
                            setAge={router.setAge}
                            duration={router.duration}
                            setDuration={router.setDuration}
                            gender={router.gender}
                            history={router.history}
                            setHistory={router.setHistory}
                            setGender={router.setGender}
                            method={router.method}
                            setMethod={router.setMethod}
                            loading={router.loading}
                            error={router.error}
                            predict={router.predict}
                            reset={router.reset}
                        />
                        {/* Feedback */}
                        {router.result && !router.fbDone && (
                            <div className="card" style={{ marginTop: 16 }}>
                                <div className="card-title">Prediction Feedback</div>
                                <p style={{ fontSize: 13, color: 'var(--slate-600)', marginBottom: 12 }}>
                                    Was this department recommendation accurate?
                                </p>
                                <div className="btn-group">
                                    <button className="btn btn-success" onClick={() => router.submitFeedback(true)}>
                                        <ThumbsUp size={14} /> Yes, correct
                                    </button>
                                    <button className="btn btn-danger" onClick={() => router.submitFeedback(false)}>
                                        <ThumbsDown size={14} /> No, incorrect
                                    </button>
                                </div>

                                {router.fbState === 'correction' && (
                                    <div style={{ marginTop: 16 }}>
                                        <label className="form-label">Correct Department</label>
                                        <select
                                            className="form-select"
                                            style={{ marginBottom: 12 }}
                                            value={router.correctDept}
                                            onChange={e => router.setCorrectDept(e.target.value)}
                                        >
                                            {DEPTS.map(d => (
                                                <option key={d} value={d}>
                                                    {d.charAt(0).toUpperCase() + d.slice(1)}
                                                </option>
                                            ))}
                                        </select>
                                        <button className="btn btn-blue" onClick={() => router.submitFeedback(false)}>
                                            Save Correction to Training Data
                                        </button>
                                    </div>
                                )}
                            </div>
                        )}

                        {router.fbDone && (
                            <div className="card" style={{ marginTop: 16, background: 'var(--green-50)', borderColor: '#86efac' }}>
                                <p style={{ fontSize: 13, color: '#065f46' }}>✓ Feedback recorded. Thank you!</p>
                            </div>
                        )}
                    </div>


                    {/* ── Result ── */}
                    <div>
                        {!router.result && !router.loading && (
                            <div className="card" style={{ textAlign: 'center', padding: '48px 24px', borderStyle: 'dashed' }}>
                                <div style={{ fontSize: 36, marginBottom: 12 }}>🏥</div>
                                <div style={{ fontSize: 14, color: 'var(--slate-400)', fontWeight: 500 }}>
                                    Fill in patient details and click<br />
                                    <strong style={{ color: 'var(--slate-600)' }}>Predict Department</strong>
                                </div>
                            </div>
                        )}

                        {router.result && (
                            <>
                                {/* Priority banner */}
                                <div className={`priority-banner ${router.priorityClass}`}>
                                    <span className="priority-badge">{router.result.priority.toUpperCase()}</span>
                                    <div className="priority-text">
                                        <div className="dept-name">
                                            {router.result.recommended.replace(/_/g, ' ').toUpperCase()}
                                        </div>
                                        <div className="dept-sub">Recommended department</div>
                                    </div>
                                    {router.result.emergency && (
                                        <span className="emergency-badge">⚠ EMERGENCY</span>
                                    )}
                                </div>

                                {/* Confidence & meta */}
                                <div className="card">
                                    <div className="result-kv">
                                        <span className="rk">ML Confidence</span>
                                        <span className="rv">{(router.result.confidence * 100).toFixed(1)}%</span>
                                    </div>
                                    <div className="result-kv">
                                        <span className="rk">Model Version</span>
                                        <span className="rv">{router.result.model_version}</span>
                                    </div>
                                    <div className="result-kv">
                                        <span className="rk">Priority Level</span>
                                        <span className="rv">{router.result.priority}</span>
                                    </div>
                                </div>

                                {/* Department ranking */}
                                <div className="card" style={{ marginTop: 14 }}>
                                    <div className="card-title">Department Ranking</div>
                                    <div className="dept-list">
                                        {router.result.departments.map((d, i) => (
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
                                {router.result.reasons?.length > 0 && (
                                    <div className="card" style={{ marginTop: 14 }}>
                                        <div className="card-title">Clinical Reasoning</div>
                                        <ul className="reasons-ul">
                                            {router.result.reasons.map((r, i) => <li key={i}>{r}</li>)}
                                        </ul>
                                    </div>
                                )}

                                {/* Warning */}
                                {router.result.warning && (
                                    <div className="warning-box" style={{ marginTop: 14 }}>
                                        <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                                        <span style={{ fontSize: 13 }}>{router.result.warning}</span>
                                    </div>
                                )}

                                {/* Raw JSON */}
                                <details>
                                    <summary>View raw API response</summary>
                                    <pre className="raw-json">{JSON.stringify(router.result, null, 2)}</pre>
                                </details>
                            </>
                        )}
                    </div>
                </div>
                </div>
            </div>
    )
}