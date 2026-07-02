import React from "react";

export interface PatientFormTypes {
    symptoms: string[]
    setSymptoms: React.Dispatch<React.SetStateAction<string[]>>

    vitals: string[]
    setVitals: React.Dispatch<React.SetStateAction<string[]>>

    age: string
    setAge: React.Dispatch<React.SetStateAction<string>>

    duration: string
    setDuration: React.Dispatch<React.SetStateAction<string>>

    gender: string
    setGender: React.Dispatch<React.SetStateAction<string>>

    history: string[]
    setHistory: React.Dispatch<React.SetStateAction<string[]>>

    method: "patient_router" | "llm" | "hybrid";
    setMethod: React.Dispatch<
        React.SetStateAction<"patient_router" | "llm" | "hybrid">
    >;

    loading: boolean
    error: string

    predict: () => void
    reset: () => void
}