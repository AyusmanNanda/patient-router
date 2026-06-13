import { useState, useEffect } from 'react'
import { Database, RefreshCw } from 'lucide-react'
import Topbar from '../components/layout/Topbar'
import { useDataManager } from '../hooks/useDataManager'

export default function DataManager() {
    const {
        loading,
        error,

        stats,
        generateResult,

        loadStats,
        generateDataset,
    } = useDataManager()

    const [rows, setRows] = useState(50000)

    useEffect(() => {
        void loadStats()
    }, [])

    return (
        <div>
            <Topbar title="Dataset Manager" subtitle="View dataset statistics and generate synthetic training data" />
            <div className="page-body">

                <div className="card">
                    <div className="card-title">Generate Dataset</div>

                    <div className="form-row" style={{ alignItems: 'flex-end' }}>
                        <div className="form-group">
                            <label className="form-label">Rows</label>
                            <input
                                type="number"
                                className="form-input"
                                value={rows}
                                min={1000}
                                step={1000}
                                onChange={(e) => setRows(Number(e.target.value))}
                            />
                        </div>

                        <div className="form-group" style={{ flex: 'none' }}>
                            <div className="btn-group">
                                <button
                                    className="btn btn-blue"
                                    disabled={loading}
                                    onClick={() => generateDataset(rows)}
                                >
                                    {loading ? <span className="spinner" /> : <Database size={14} />}
                                    Generate Dataset
                                </button>

                                <button
                                    className="btn btn-ghost"
                                    disabled={loading}
                                    onClick={loadStats}
                                >
                                    <RefreshCw size={14} />
                                    Refresh Stats
                                </button>
                            </div>
                        </div>
                    </div>

                    {error && <div className="error-box">{error}</div>}
                </div>

                {generateResult && (
                    <div className="priority-banner priority-low">
                        <span className="priority-badge">{generateResult.status}</span>
                        <div className="priority-text">
                            <div className="dept-name">Dataset generated</div>
                            <div className="dept-sub">
                                {generateResult.rows_generated.toLocaleString()} rows generated
                            </div>
                        </div>
                    </div>
                )}

                {stats && (
                    <>
                        <div className="stat-grid">
                            <div className="stat-card">
                                <div className="stat-label">Total Rows</div>
                                <div className="stat-value">{stats.total_rows.toLocaleString()}</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-label">Total Columns</div>
                                <div className="stat-value">{stats.total_columns}</div>
                            </div>
                        </div>

                        <div className="two-col">
                            <div className="card">
                                <div className="card-title">Department Distribution</div>
                                <div className="data-table-wrap">
                                    <table className="data-table">
                                        <thead>
                                        <tr>
                                            <th>Department</th>
                                            <th>Count</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {Object.entries(stats.departments).map(([dept, count]) => (
                                            <tr key={dept}>
                                                <td style={{ textTransform: 'capitalize' }}>
                                                    {dept.replace(/_/g, ' ')}
                                                </td>
                                                <td>{count}</td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            <div className="card">
                                <div className="card-title">Priority Distribution</div>
                                <div className="data-table-wrap">
                                    <table className="data-table">
                                        <thead>
                                        <tr>
                                            <th>Priority</th>
                                            <th>Count</th>
                                        </tr>
                                        </thead>
                                        <tbody>
                                        {Object.entries(stats.priorities).map(([priority, count]) => (
                                            <tr key={priority}>
                                                <td style={{ textTransform: 'capitalize' }}>{priority}</td>
                                                <td>{count}</td>
                                            </tr>
                                        ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    )
}