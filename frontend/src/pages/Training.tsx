import { Cpu } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { useTraining } from '../hooks/useTraining'

export default function Training() {
    const { loading, error, status, result, train } = useTraining()

    return (
        <div>
            <Topbar title="Model Training" subtitle="Retrain the model using the current dataset" />
            <div className="page-body">

                {status === 'training' && (
                    <div className="priority-banner priority-medium">
                        <span className="priority-badge">Running</span>
                        <div className="priority-text">
                            <div className="dept-name">Training in progress</div>
                            <div className="dept-sub">This may take a few minutes — feel free to navigate away</div>
                        </div>
                    </div>
                )}

                {status === 'success' && result && (
                    <div className="priority-banner priority-low">
                        <span className="priority-badge">Done</span>
                        <div className="priority-text">
                            <div className="dept-name">Model retrained successfully</div>
                            <div className="dept-sub">New model is ready to use</div>
                        </div>
                    </div>
                )}

                <div className="card">
                    <div className="card-title">Run Training</div>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14 }}>
                        This will retrain the triage model using the latest collected feedback and dataset.
                    </p>
                    <button className="btn btn-blue" onClick={train} disabled={loading}>
                        {loading ? <span className="spinner" /> : <Cpu size={14} />}
                        {loading ? 'Training Model...' : 'Train Model'}
                    </button>

                    {status === 'error' && error && (
                        <div className="error-box">{error}</div>
                    )}
                </div>

                {status === 'success' && result && (
                    <>
                        <div className="card">
                            <div className="card-title">Accuracy</div>
                            <div className="dept-list">
                                <div className="dept-row">
                                    <span className="dept-name-text">Training Accuracy</span>
                                    <div className="dept-bar-wrap">
                                        <div className="dept-bar-fill" style={{ width: `${result.train_accuracy}%` }} />
                                    </div>
                                    <span className="dept-pct">{result.train_accuracy}%</span>
                                </div>
                                <div className="dept-row">
                                    <span className="dept-name-text">Testing Accuracy</span>
                                    <div className="dept-bar-wrap">
                                        <div className="dept-bar-fill" style={{ width: `${result.test_accuracy}%` }} />
                                    </div>
                                    <span className="dept-pct">{result.test_accuracy}%</span>
                                </div>
                            </div>
                        </div>

                        <div className="stat-grid">
                            <div className="stat-card">
                                <div className="stat-label">Dataset Size</div>
                                <div className="stat-value">{result.dataset_size.toLocaleString()}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Training Time</div>
                                <div className="stat-value">{result.training_time_insec}s</div>
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