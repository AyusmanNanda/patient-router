import { Cpu } from 'lucide-react'
import { useTraining } from '../hooks/useTraining'

export default function Training() {
    const {
        loading,
        error,
        status,
        result,
        train,
    } = useTraining()

    return (
        <div className="page">
            <div className="page-header">
                <h1>Model Training</h1>
                <p>
                    Retrain the model using the current dataset.
                </p>
            </div>

            <div className="card">
                <button
                    className="primary-btn"
                    onClick={train}
                    disabled={loading}
                >
                    <Cpu size={18} />

                    {loading
                        ? 'Training Model...'
                        : 'Train Model'}
                </button>
            </div>

            {status === 'training' && (
                <div className="card">
                    <h3>Training In Progress</h3>
                    <p>
                        The model is currently being retrained.
                        Please wait...
                    </p>
                </div>
            )}

            {error && (
                <div className="card error-card">
                    <h3>Training Failed</h3>
                    <p>{error}</p>
                </div>
            )}

            {result && (
                <div className="card">
                    <h2>Training Results</h2>

                    <div className="stats-grid">

                        <div className="stat-item">
                            <span className="stat-label">
                                Training Accuracy
                            </span>

                            <span className="stat-value">
                                {result.train_accuracy}%
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                Testing Accuracy
                            </span>

                            <span className="stat-value">
                                {result.test_accuracy}%
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                Dataset Size
                            </span>

                            <span className="stat-value">
                                {result.dataset_size.toLocaleString()}
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                Training Time
                            </span>

                            <span className="stat-value">
                                {result.training_time_insec}s
                            </span>
                        </div>

                    </div>
                </div>
            )}
        </div>
    )
}