export interface LogEntry {
    age: number
    confidence: number
    duration: number
    emergency: boolean
    fallback_used: boolean
    gender: string
    model_version: string
    priority: string
    recommended: string
    symptoms: string[]
    timestamp: string
    vitals: string[]
}

export interface LogsResponse {
    logs: LogEntry[]
    total_emergencies: number
    total_fallbacks: number
    total_predictions: number
}