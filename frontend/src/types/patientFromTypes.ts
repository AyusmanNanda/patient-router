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

    loading: boolean
    error: string

    predict: () => void
    reset: () => void
}