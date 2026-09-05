
import { apiClient } from './client';

export interface SimulationResult {
    simulation_id: string;
    simulation_status: string;
    baseline_metrics: Record<string, any>;
    assumptions: string[];
    simulated_metrics: Record<string, any>;
    confidence: string;
}

export const runSimulation = async (merchant_id: string, opportunity_id: string): Promise<SimulationResult> => {
    const { data } = await apiClient.post('/api/growth/simulate', { merchant_id, opportunity_id });
    return data;
};

export const executeStrategy = async (merchant_id: string, opportunity_id: string, approval_id: string, idempotency_key: string): Promise<any> => {
    const headers = { 'idempotency-key': idempotency_key };
    const { data } = await apiClient.post('/api/growth/executions', { merchant_id, opportunity_id, approval_id }, { headers });
    return data;
};

export const fetchAuditLogs = async (merchant_id: string): Promise<any[]> => {
    const { data } = await apiClient.get(`/api/growth/audit?merchant_id=${merchant_id}`);
    return data;
};
