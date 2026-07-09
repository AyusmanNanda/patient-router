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
export interface ModelComparison {
    Model: string
    'Test Accuracy (%)': number
    'Macro F1 (%)': number
    '5-Fold CV (%)': number
    'CV Std (±%)': number
    'Edge-Case Acc (%)': number
    'Generalisation Gap': number
    'Train Time (s)': number
}