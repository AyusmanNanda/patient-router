export interface EvaluationResponse {
    synthetic_accuracy: number
    cv_accuracy: number
    cv_std: number

    edge_case_accuracy: number
    generalization_gap: number

    total_edge_cases: number
    passed_edge_cases: number
    failed_edge_cases: number
}