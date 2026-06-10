export interface DataStatsResponse {
    total_rows: number
    total_columns: number

    departments: Record<string, number>
    priorities: Record<string, number>
}

export interface GenerateDataResponse {
    status: string
    rows_generated: number
}