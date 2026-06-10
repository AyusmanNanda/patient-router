import { Trash2 } from 'lucide-react'
import { useLogs } from '../hooks/useLogs'

export default function Logs() {
    const {
        loading,
        error,
        data,
        clearLogs,
    } = useLogs()

    return (
        <div className="page">

            <div className="page-header">
                <h1>System Logs</h1>
                <p>
                    Prediction history and usage statistics.
                </p>
            </div>

            {loading && (
                <div className="card">
                    Loading logs...
                </div>
            )}

            {error && (
                <div className="card error-card">
                    {error}
                </div>
            )}

            {data && (
                <>
                    <div className="stats-grid">

                        <div className="stat-item">
                            <span>Total Predictions</span>
                            <strong>
                                {data.total_predictions}
                            </strong>
                        </div>

                        <div className="stat-item">
                            <span>Emergencies</span>
                            <strong>
                                {data.total_emergencies}
                            </strong>
                        </div>

                        <div className="stat-item">
                            <span>Fallbacks</span>
                            <strong>
                                {data.total_fallbacks}
                            </strong>
                        </div>

                    </div>

                    <div className="card">

                        <button
                            className="danger-btn"
                            onClick={clearLogs}
                        >
                            <Trash2 size={16} />
                            Clear Logs
                        </button>

                    </div>

                    <div className="card">

                        <h2>Prediction History</h2>

                        <table>
                            <thead>
                            <tr>
                                <th>Department</th>
                                <th>Priority</th>
                                <th>Emergency</th>
                                <th>Confidence</th>
                                <th>Age</th>
                            </tr>
                            </thead>

                            <tbody>
                            {data.logs.map(
                                (log, index) => (
                                    <tr key={index}>
                                        <td>
                                            {log.recommended}
                                        </td>

                                        <td>
                                            {log.priority}
                                        </td>

                                        <td>
                                            {log.emergency
                                                ? 'Yes'
                                                : 'No'}
                                        </td>

                                        <td>
                                            {(
                                                log.confidence * 100
                                            ).toFixed(1)}
                                            %
                                        </td>

                                        <td>
                                            {log.age}
                                        </td>
                                    </tr>
                                )
                            )}
                            </tbody>
                        </table>

                    </div>
                </>
            )}
        </div>
    )
}