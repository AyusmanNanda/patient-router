import { useState } from 'react'
import { Database, RefreshCw } from 'lucide-react'
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
    const [initialized, setInitialized] =
        useState(false)

    if (!initialized) {
        setInitialized(true)
        void loadStats()
    }

    return (
        <div className="page">

            <div className="page-header">
                <h1>Dataset Manager</h1>

                <p>
                    View dataset statistics and
                    generate synthetic training data.
                </p>
            </div>

            <div className="card">

                <h2>Generate Dataset</h2>

                <div className="generate-controls">

                    <input
                        type="number"
                        value={rows}
                        min={1000}
                        step={1000}
                        onChange={(e) =>
                            setRows(Number(e.target.value))
                        }
                    />

                    <button
                        className="primary-btn"
                        disabled={loading}
                        onClick={() =>
                            generateDataset(rows)
                        }
                    >
                        <Database size={18} />
                        Generate Dataset
                    </button>

                    <button
                        className="secondary-btn"
                        disabled={loading}
                        onClick={loadStats}
                    >
                        <RefreshCw size={18} />
                        Refresh Stats
                    </button>

                </div>

            </div>

            {error && (
                <div className="card error-card">
                    {error}
                </div>
            )}

            {generateResult && (
                <div className="card">

                    <h2>Generation Result</h2>

                    <p>
                        Status:
                        {' '}
                        <strong>
                            {generateResult.status}
                        </strong>
                    </p>

                    <p>
                        Rows Generated:
                        {' '}
                        <strong>
                            {generateResult.rows_generated.toLocaleString()}
                        </strong>
                    </p>

                </div>
            )}

            {stats && (
                <>
                    <div className="stats-grid">

                        <div className="stat-item">
                            <span className="stat-label">
                                Total Rows
                            </span>

                            <span className="stat-value">
                                {stats.total_rows.toLocaleString()}
                            </span>
                        </div>

                        <div className="stat-item">
                            <span className="stat-label">
                                Total Columns
                            </span>

                            <span className="stat-value">
                                {stats.total_columns}
                            </span>
                        </div>

                    </div>

                    <div className="card">

                        <h2>
                            Department Distribution
                        </h2>

                        <table>
                            <thead>
                            <tr>
                                <th>Department</th>
                                <th>Count</th>
                            </tr>
                            </thead>

                            <tbody>
                            {Object.entries(
                                stats.departments
                            ).map(
                                ([dept, count]) => (
                                    <tr key={dept}>
                                        <td>{dept}</td>
                                        <td>{count}</td>
                                    </tr>
                                )
                            )}
                            </tbody>
                        </table>

                    </div>

                    <div className="card">

                        <h2>
                            Priority Distribution
                        </h2>

                        <table>
                            <thead>
                            <tr>
                                <th>Priority</th>
                                <th>Count</th>
                            </tr>
                            </thead>

                            <tbody>
                            {Object.entries(
                                stats.priorities
                            ).map(
                                ([priority, count]) => (
                                    <tr key={priority}>
                                        <td>{priority}</td>
                                        <td>{count}</td>
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