
import { apiClient } from './client';

export interface ScoreComponents {
    evidence_strength: number;
    population_relevance: number;
    business_value_signal: number;
    confidence: number;
    risk_penalty: number;
    final_score: number;
}

export interface Opportunity {
    id: string;
    title: string;
    type: string;
    description: string;
    evidence: Record<string, any>;
    score: number;
    confidence: number;
    risk: string;
    recommended_action: string;
    status: string;
    requires_approval: boolean;
    prediction_status: string;
}

export interface AgentRun {
    run_id: string;
    status: string;
    started_at: string;
    ended_at: string;
    output_summary: string;
}

export interface AgentAction {
    id: string;
    step: string;
    tool_name: string;
    input_summary: string;
    output_summary: string;
    status: string;
    created_at: string;
}

export const runGrowthAgent = async (merchant_id: string, idempotencyKey?: string): Promise<any> => {
    const headers = idempotencyKey ? { 'idempotency-key': idempotencyKey } : {};
    const { data } = await apiClient.post('/api/agents/growth/run', { merchant_id }, { headers });
    return data;
};

export const fetchOpportunities = async (merchant_id: string): Promise<Opportunity[]> => {
    const { data } = await apiClient.get(`/api/agents/growth/opportunities?merchant_id=${merchant_id}`);
    return data;
};

export const fetchAgentRuns = async (merchant_id: string): Promise<AgentRun[]> => {
    const { data } = await apiClient.get(`/api/agents/runs?merchant_id=${merchant_id}`);
    return data;
};

export const fetchRunActions = async (run_id: string): Promise<AgentAction[]> => {
    const { data } = await apiClient.get(`/api/agents/runs/${run_id}/actions`);
    return data;
};
