import TagInput from "../layout/TagInput.tsx";
import { VITALS, SYMPTOMS } from "../../constants/patientOptions.ts";
import { Send, RotateCcw } from "lucide-react";

export default function PatientForm (props) {
    return (
        <div className="card">
            <div className="card-title">
                <span>Patient Information</span>
            </div>

            <div className="form-group">
                <label className="form-label">Symptoms <span className="req">*</span></label>
                <TagInput
                    options={SYMPTOMS}
                    value={props.symptoms}
                    onChange={props.setSymptoms}
                    placeholder="Type to search symptoms…"
                />
            </div>

            <div className="form-group">
                <label className="form-label">Vital Signs</label>
                <TagInput
                    options={VITALS}
                    value={props.vitals}
                    onChange={props.setVitals}
                    placeholder="Type to search vitals…"
                />
            </div>

            <div className="form-row" style={{ marginBottom: 18 }}>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Age <span className="req">*</span></label>
                    <input
                        className="form-input"
                        type="number"
                        min={0}
                        max={120}
                        placeholder="e.g. 45"
                        value={props.age}
                        onChange={e => props.setAge(e.target.value)}
                    />
                </div>
                <div className="form-group" style={{ marginBottom: 0 }}>
                    <label className="form-label">Gender</label>
                    <select className="form-select" value={props.gender} onChange={e => props.setGender(e.target.value)}>
                        <option value="male">Male</option>
                        <option value="female">Female</option>
                        <option value="other">Other</option>
                    </select>
                </div>
            </div>

            <div className="form-group">
                <label className="form-label">Duration (days) <span className="req">*</span></label>
                <input
                    className="form-input"
                    type="number"
                    min={0}
                    placeholder="e.g. 3"
                    value={props.duration}
                    onChange={e => props.setDuration(e.target.value)}
                />
            </div>
            {props.error && <div className="error-box">⚠ {props.error}</div>}

            <div className="btn-group" style={{ marginTop: 6 }}>
                <button
                    className="btn btn-primary btn-lg"
                    onClick={props.predict}
                    disabled={props.loading}
                    style={{ flex: 1 }}
                >
                    {props.loading
                        ? <><span className="spinner" /> Analyzing…</>
                        : <><Send size={14} /> Predict Department</>
                    }
                </button>
                <button className="btn btn-ghost" onClick={props.reset}>
                    <RotateCcw size={14} /> Reset
                </button>
            </div>
        </div>
            )
}