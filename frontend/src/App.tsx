import { Routes, Route } from 'react-router-dom'
import { WifiOff } from 'lucide-react'

import Sidebar from './components/layout/Sidebar'
import PatientRouter from './pages/PatientRouter.tsx'
import Training from './pages/Training'
import Logs from './pages/Logs'
import Evalution from './pages/Evaluation.tsx'
import DataManager from './pages/DataManger'
import { useBackendStatus } from './hooks/useBackendStatus'

export default function App() {
    const {
        isOffline,
        checking,
        checkConnection,
    } = useBackendStatus()

    return (
        <div className="shell">
            <Sidebar />

            <main className="main-content">
                <Routes>
                    <Route path="/" element={<PatientRouter />} />
                    <Route path="/training" element={<Training />} />
                    <Route path="/logs" element={<Logs />} />
                    <Route path="/evaluate" element={<Evalution />} />
                    <Route path="/data" element={<DataManager />} />
                </Routes>
            </main>

            {isOffline && (
                <div className="backend-overlay">
                    <div className="backend-modal">
                        <div className="backend-modal-icon">
                            <WifiOff size={28} />
                        </div>

                        <div className="backend-modal-title">
                            Backend Unavailable
                        </div>

                        <p className="backend-modal-text">
                            Patient Router cannot connect to the backend server.
                            Check your connection or make sure the backend is running.
                        </p>

                        <button
                            className="btn btn-blue"
                            onClick={() => void checkConnection()}
                            disabled={checking}
                        >
                            {checking
                                ? 'Checking Connection...'
                                : 'Retry Connection'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}