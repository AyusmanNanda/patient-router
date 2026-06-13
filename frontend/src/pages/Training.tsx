import { Cpu, AlertTriangle, CheckCircle2, Database, Clock, Target } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { useTraining } from '../hooks/useTraining'

export default function Training() {
    const { loading, error, status, result, train } = useTraining()

    return (
        <div>
            <Topbar title="Model Training" subtitle="Retrain the model using the current dataset" />
            <div className="page-body">

                {/* Status banner */}
                {status === 'training' && (
                    <div className="priority-banner priority-amber">
                        <span className="priority-badge">RUNNING</span>
                        <div className="priority-text">
                            <div className="dept-name">TRAINING IN PROGRESS</div>
                            <div className="dept-sub">This may take a few minutes...</div>
                        </div>
                    </div>
                )}

                {status === 'success' && result && (
                    <div className="priority-banner priority-green">
                        <span className="priority-badge">
                            <CheckCircle2 size={14} /> DONE
                        </span>
                        <div className="priority-text">
                            <div className="dept-name">MODEL RETRAINED SUCCESSFULLY</div>
                            <div className="dept-sub">New model is ready to use</div>
                        </div>
                    </div>
                )}

                {/* Trigger */}
                <div className="card" style={{ marginTop: status === 'idle' ? 0 : 14 }}>
                    <div className="card-title">Run Training</div>
                    <p style={{ fontSize: 13, color: 'var(--slate-600)', marginBottom: 12 }}>
                        This will retrain the triage model using the latest collected feedback and dataset.
                    </p>
                    <button className="btn btn-blue" onClick={train} disabled={loading}>
                        <Cpu size={16} />
                        {loading ? 'Training Model...' : 'Train Model'}
                    </button>
                </div>

                {/* Error */}
                {status === 'error' && error && (
                    <div className="warning-box" style={{ marginTop: 14 }}>
                        <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 1 }} />
                        <span style={{ fontSize: 13 }}>{error}</span>
                    </div>
                )}

                {/* Results */}
                {status === 'success' && result && (
                    <>
                        <div className="card" style={{ marginTop: 14 }}>
                            <div className="card-title">Accuracy</div>
                            <div className="dept-list">
                                <div className="dept-row">
                                    <span className="dept-rank"><Target size={14} /></span>
                                    <span className="dept-name-text">Training Accuracy</span>
                                    <div className="dept-bar-wrap">
                                        <div className="dept-bar-fill" style={{ width: `${result.train_accuracy}%` }} />
                                    </div>
                                    <span className="dept-pct">{result.train_accuracy}%</span>
                                </div>
                                <div className="dept-row">
                                    <span className="dept-rank"><Target size={14} /></span>
                                    <span className="dept-name-text">Testing Accuracy</span>
                                    <div className="dept-bar-wrap">
                                        <div className="dept-bar-fill" style={{ width: `${result.test_accuracy}%` }} />
                                    </div>
                                    <span className="dept-pct">{result.test_accuracy}%</span>
                                </div>
                            </div>
                        </div>

                        <div className="card" style={{ marginTop: 14 }}>
                            <div className="result-kv">
                                <span className="rk">
                                    <Database size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
                                    Dataset Size
                                </span>
                                <span className="rv">{result.dataset_size.toLocaleString()}</span>
                            </div>
                            <div className="result-kv">
                                <span className="rk">
                                    <Clock size={14} style={{ marginRight: 6, verticalAlign: -2 }} />
                                    Training Time
                                </span>
                                <span className="rv">{result.training_time_insec}s</span>
                            </div>
                        </div>

                        <details>
                            <summary>View raw API response</summary>
                            <pre className="raw-json">{JSON.stringify(result, null, 2)}</pre>
                        </details>
                    </>
                )}
            </div>
        </div>
    )
}