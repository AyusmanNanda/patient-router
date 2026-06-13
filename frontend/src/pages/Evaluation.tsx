import { useEffect } from 'react'
import { BarChart3 } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { useEvaluation } from '../hooks/useEvaluation'

export default function Evaluation() {
    const {
        loading,
        error,
        result,
        loadEvaluation,
    } = useEvaluation()

    useEffect(() => {
        void loadEvaluation()
    }, [])

    const BACKEND_URL = import.meta.env.VITE_BACKEND

    return (
        <div>
            <Topbar title="Model Evaluation" subtitle="Evaluation metrics, confusion matrix, and generated reports" />
            <div className="page-body">

                <div className="card">
                    <button
                        className="btn btn-blue"
                        onClick={loadEvaluation}
                        disabled={loading}
                    >
                        {loading ? <span className="spinner" /> : <BarChart3 size={14} />}
                        {loading ? 'Loading Evaluation...' : 'Refresh Evaluation'}
                    </button>
                </div>

                {error && <div className="error-box">{error}</div>}

                {result && (
                    <>
                        <div className="stat-grid">
                            <div className="stat-card">
                                <div className="stat-label">Synthetic Accuracy</div>
                                <div className="stat-value">{result.synthetic_accuracy}%</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">CV Accuracy</div>
                                <div className="stat-value">{result.cv_accuracy}%</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Edge Case Accuracy</div>
                                <div className="stat-value">{result.edge_case_accuracy}%</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Generalization Gap</div>
                                <div className="stat-value">{result.generalization_gap}</div>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-title">Edge Case Testing</div>
                            <div className="result-kv">
                                <span className="rk">Passed</span>
                                <span className="rv">{result.passed_edge_cases}</span>
                            </div>
                            <div className="result-kv">
                                <span className="rk">Failed</span>
                                <span className="rv">{result.failed_edge_cases}</span>
                            </div>
                            <div className="result-kv">
                                <span className="rk">Total</span>
                                <span className="rv">{result.total_edge_cases}</span>
                            </div>
                            <div className="result-kv">
                                <span className="rk">CV Standard Deviation</span>
                                <span className="rv">{result.cv_std}</span>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-title">Confusion Matrix</div>
                            <img
                                src={`${BACKEND_URL}/evaluation/confusion-matrix`}
                                alt="Confusion Matrix"
                                style={{ maxWidth: '100%', borderRadius: 'var(--r-md)' }}
                            />
                        </div>

                        <div className="card">
                            <div className="card-title">Evaluation Report</div>
                            <img
                                src={`${BACKEND_URL}/evaluation/report-image`}
                                alt="Evaluation Report"
                                style={{ maxWidth: '100%', borderRadius: 'var(--r-md)' }}
                            />
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}