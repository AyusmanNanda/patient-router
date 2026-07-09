interface Props {
    title: string
    subtitle?: string
}

export default function Topbar({ title, subtitle }: Props) {
    return (
        <>
            <div className="topbar">
                <div className="topbar-breadcrumb">
                    <span>PatientRouter</span>
                    <span style={{ color: '#cbd5e1' }}>›</span>
                    <strong>{title}</strong>
                </div>
            </div>

            <div className="page-header">
                <div className="page-title">{title}</div>

                {subtitle && (
                    <div className="page-subtitle">
                        {subtitle}
                    </div>
                )}
            </div>
        </>
    )
}