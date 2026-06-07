export interface patientFormTypes {
    symptoms: string[]
    setSymptoms: (value: string[]) => void

    vitals: string[]
    setVitals: (value: string[]) => void

    age: string
    setAge: (value: string) => void

    duration: string
    setDuration: (value: string) => void

    gender: string
    setGender: (value: string) => void

    loading: boolean
    error: string

    predict: () => void
    reset: () => void
}