import { Routes, Route } from 'react-router-dom'
import Sidebar       from './components/layout/Sidebar.tsx'
import PatientRouter from './pages/patientRouter.tsx'

export default function App() {
    return (
        <div className="shell">
            <Sidebar />
            <main className="main-content">
                <Routes>
                    <Route path="/" element={<PatientRouter />} />
                </Routes>
            </main>
        </div>
    )
}
