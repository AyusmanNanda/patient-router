export interface DepartmentScore {
    department: string;
    confidence: number;
}

export interface PredictResponse {
    recommended: string;
    confidence: number;
    priority: "high" | "medium" | "low";
    emergency: boolean;
    model_version: string;
    departments: DepartmentScore[];
    reasons: string[];
    warning?: string;
}

export interface PredictRequest {
    symptoms: string;
    vitals: string;
    age: number;
    duration: number;
    gender: string;
}

export interface FeedbackRequest {
    symptoms: string;
    vitals: string;
    age: number;
    duration: number;
    gender: string;
    priority: string;
    correct_department: string;
}

export interface FeedbackResponse {
    message: string;
}