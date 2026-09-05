
import { apiClient } from './client';

export interface Approval {
    id: string;
    opportunity_id: string;
    action_description: string;
    reason: string;
    status: string;
    requested_at: string;
    risk: string;
    evidence_snapshot: Record<string, any>;
}

export const requestApproval = async (merchant_id: string, opportunity_id: string): Promise<{approval_id: string}> => {
    const { data } = await apiClient.post('/api/approvals', { merchant_id, opportunity_id });
    return data;
};

export const fetchApprovals = async (merchant_id: string): Promise<Approval[]> => {
    const { data } = await apiClient.get(`/api/approvals?merchant_id=${merchant_id}`);
    return data;
};

export const approveRequest = async (approval_id: string): Promise<void> => {
    await apiClient.post(`/api/approvals/${approval_id}/approve`);
};

export const rejectRequest = async (approval_id: string, reason: string): Promise<void> => {
    await apiClient.post(`/api/approvals/${approval_id}/reject`, { reason });
};
