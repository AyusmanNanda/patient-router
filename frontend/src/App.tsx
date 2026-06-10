import { Routes, Route } from 'react-router-dom'
import Sidebar       from './components/layout/Sidebar'
import PatientRouter from './pages/patientRouter'
import Training from "./pages/Training"
import Logs from "./pages/Logs"
import Evalution from "./pages/Evalution"

export default function App() {
    return (
        <div className="shell">
            <Sidebar />
            <main className="main-content">
                <Routes>
                    <Route path="/" element={<PatientRouter />} />
                    <Route path="/training" element={<Training />} />
                    <Route path="/logs" element={<Logs />} />
                    <Route path="/evaluate" element={<Evalution />} />
                </Routes>
            </main>
        </div>
    )
}
