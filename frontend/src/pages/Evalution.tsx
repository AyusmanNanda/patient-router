import { useState } from 'react'
import { BarChart3 } from 'lucide-react'
import { useEvaluation } from '../hooks/useEvaluation'

export default function Evaluation() {
    const {
        loading,
        error,
        result,
        loadEvaluation,
    } = useEvaluation()

    const [initialized, setInitialized] =
        useState(false)

    if (!initialized) {
        setInitialized(true)
        void loadEvaluation()
    }

    return (
        <div className="page">

            <div className="page-header">
                <h1>Model Evaluation</h1>

                <p>
                    Evaluation metrics, confusion matrix,
                    and generated reports.
                </p>
            </div>

            <div className="card">
                <button
                    className="primary-btn"
                    onClick={loadEvaluation}
                    disabled={loading}
                >
                    <BarChart3 size={18} />

                    {loading
                        ? 'Loading Evaluation...'
                        : 'Refresh Evaluation'}
                </button>
            </div>

            {error && (
                <div className="card error-card">
                    <p>{error}</p>
                </div>
            )}

            {result && (
                <>
                    <div className="stats-grid">

                        <div className="stat-item">
                            <span className="stat-label">
                                Synthetic Accuracy
                            </span>

                            <span className="stat-value">
                                {result.synthetic_accuracy}%
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                CV Accuracy
                            </span>

                            <span className="stat-value">
                                {result.cv_accuracy}%
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                Edge Case Accuracy
                            </span>

                            <span className="stat-value">
                                {result.edge_case_accuracy}%
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                Generalization Gap
                            </span>

                            <span className="stat-value">
                                {result.generalization_gap}
                            </span>
                        </div>

                    </div>

                    <div className="card">
                        <h2>Edge Case Testing</h2>

                        <p>
                            Passed: {result.passed_edge_cases}
                        </p>

                        <p>
                            Failed: {result.failed_edge_cases}
                        </p>

                        <p>
                            Total: {result.total_edge_cases}
                        </p>

                        <p>
                            CV Standard Deviation:
                            {' '}
                            {result.cv_std}
                        </p>
                    </div>

                    <div className="card">
                        <h2>Confusion Matrix</h2>

                        <img
                            src="http://127.0.0.1:5000/evaluation/confusion-matrix"
                            alt="Confusion Matrix"
                            style={{
                                maxWidth: '100%',
                            }}
                        />
                    </div>

                    <div className="card">
                        <h2>Evaluation Report</h2>

                        <img
                            src="http://127.0.0.1:5000/evaluation/report-image"
                            alt="Evaluation Report"
                            style={{
                                maxWidth: '100%',
                            }}
                        />
                    </div>

                </>
            )}
        </div>
    )
}