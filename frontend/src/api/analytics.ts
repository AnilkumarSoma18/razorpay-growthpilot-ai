
import { apiClient } from './client';

export interface HealthResponse {
  status: string;
  app_env: string;
  database: string;
  timestamp: string;
}

export interface RevenueMetrics {
  is_synthetic_demo_data: boolean;
  total_revenue: number;
  order_count: number;
  paid_order_count: number;
  failed_order_count: number;
  refunded_order_count: number;
  period_start?: string;
  period_end?: string;
}

export interface ConversionMetrics {
  is_synthetic_demo_data: boolean;
  converted_carts: number;
  abandoned_carts: number;
  total_carts: number;
  conversion_rate_percent: number;
  cart_abandonment_rate_percent: number;
}

export interface AOVMetrics {
  is_synthetic_demo_data: boolean;
  average_order_value: number;
  paid_order_count: number;
}

export interface RetentionMetrics {
  is_synthetic_demo_data: boolean;
  total_customers: number;
  returning_customers: number;
  returning_customer_rate_percent: number;
}

export interface DashboardSummary {
  is_synthetic_demo_data: boolean;
  revenue: RevenueMetrics;
  conversion: ConversionMetrics;
  aov: AOVMetrics;
  retention: RetentionMetrics;
}

let merchantIdCache: string | null = null;

export const getDemoMerchantId = async (): Promise<string> => {
    if (merchantIdCache) return merchantIdCache;
    const res = await apiClient.get<{id: string}>('/api/merchants/demo');
    merchantIdCache = res.data.id;
    return merchantIdCache;
};

export const fetchHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get('/health');
  return data;
};

export const fetchDashboardSummary = async (): Promise<DashboardSummary> => {
  const mId = await getDemoMerchantId();
  const { data } = await apiClient.get(`/api/dashboard/summary?merchant_id=${mId}`);
  return data;
};
