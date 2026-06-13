import { Trash2 } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { useLogs } from '../hooks/useLogs'

function priorityBadgeClass(priority: string) {
    switch (priority) {
        case 'high':
        case 'emergency':
            return 'badge-red'
        case 'medium':
            return 'badge-amber'
        case 'low':
            return 'badge-green'
        default:
            return 'badge-slate'
    }
}

export default function Logs() {
    const { loading, error, data, clearLogs } = useLogs()

    return (
        <div>
            <Topbar title="System Logs" subtitle="Prediction history and usage statistics" />
            <div className="page-body">

                {loading && (
                    <div className="card">
                        <div className="card-title">Loading logs...</div>
                    </div>
                )}

                {error && <div className="error-box">{error}</div>}

                {data && (
                    <>
                        <div className="stat-grid">
                            <div className="stat-card">
                                <div className="stat-label">Total Predictions</div>
                                <div className="stat-value">{data.total_predictions}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Emergencies</div>
                                <div className="stat-value">{data.total_emergencies}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Fallbacks</div>
                                <div className="stat-value">{data.total_fallbacks}</div>
                            </div>
                        </div>

                        <div className="card">
                            <div className="card-title">Prediction History</div>

                            <div className="data-table-wrap">
                                <table className="data-table">
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
                                    {data.logs.map((log, index) => (
                                        <tr key={index}>
                                            <td style={{ textTransform: 'capitalize' }}>
                                                {log.recommended.replace(/_/g, ' ')}
                                            </td>
                                            <td>
                                                    <span className={`badge ${priorityBadgeClass(log.priority)}`}>
                                                        {log.priority}
                                                    </span>
                                            </td>
                                            <td>
                                                {log.emergency
                                                    ? <span className="badge badge-red">Yes</span>
                                                    : <span className="badge badge-slate">No</span>}
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                                    <div className="progress-wrap" style={{ width: 80 }}>
                                                        <div
                                                            className="progress-bar"
                                                            style={{ width: `${(log.confidence * 100).toFixed(0)}%` }}
                                                        />
                                                    </div>
                                                    <span className="dept-pct">{(log.confidence * 100).toFixed(1)}%</span>
                                                </div>
                                            </td>
                                            <td>{log.age}</td>
                                        </tr>
                                    ))}
                                    </tbody>
                                </table>
                            </div>

                            <div style={{ marginTop: 14 }}>
                                <button className="btn btn-danger btn-sm" onClick={clearLogs}>
                                    <Trash2 size={14} />
                                    Clear Logs
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}