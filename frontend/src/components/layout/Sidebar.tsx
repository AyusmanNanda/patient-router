import { NavLink, useLocation } from 'react-router-dom'
import { Stethoscope, Cpu, FileText, BarChart3, Database } from 'lucide-react'

const NAV = [
    { path: '/',         label: 'Patient Router', icon: Stethoscope },
    { path: '/training', label: 'Train Model',    icon: Cpu         },
    { path: '/logs',     label: 'System Logs',    icon: FileText    },
    { path: '/evaluate', label: 'Evaluation',     icon: BarChart3   },
    { path: '/data',     label: 'Data Manager',   icon: Database    },
]

export default function Sidebar() {
    const loc = useLocation()
    return (
        <aside className="sidebar">
            <div className="sidebar-header">
                <div className="sidebar-title">Patient Router</div>
                <div className="sidebar-sub">Clinical Decision Support</div>
            </div>

            <nav className="sidebar-nav">
                {NAV.map(({ path, label, icon: Icon }) => (
                    <NavLink
                        key={path}
                        to={path}
                        end={path === '/'}
                        className={({ isActive }) =>
                            'nav-link' + (isActive || (path !== '/' && loc.pathname.startsWith(path)) ? ' active' : '')
                        }
                    >
                        <Icon size={15} strokeWidth={1.75} />
                        {label}
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
            </div>
        </aside>
    )
}