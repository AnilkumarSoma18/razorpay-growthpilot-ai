
import { useQuery } from "@tanstack/react-query"
import { fetchDashboardSummary } from "@/api/analytics"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function Dashboard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: fetchDashboardSummary
  })

  if (isLoading) return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading analytics...</div>
  if (isError) return <div className="p-8 text-center text-red-500 border border-red-200 bg-red-50 rounded-lg">Failed to load analytics. Is the backend running?</div>
  if (!data) return null

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Merchant Dashboard</h1>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{(data.revenue.total_revenue).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
            <p className="text-xs text-muted-foreground pt-1">
              {data.revenue.paid_order_count} paid orders
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Conversion Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.conversion.conversion_rate_percent.toFixed(2)}%</div>
            <p className="text-xs text-muted-foreground pt-1">
              {data.conversion.cart_abandonment_rate_percent.toFixed(2)}% cart abandonment
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Order Value</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">₹{(data.aov.average_order_value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Returning Customers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.retention.returning_customer_rate_percent.toFixed(2)}%</div>
            <p className="text-xs text-muted-foreground pt-1">
              {data.retention.returning_customers} of {data.retention.total_customers} total
            </p>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
          <Card className="col-span-4">
            <CardHeader>
              <CardTitle>Revenue Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border border-dashed rounded-md bg-muted/10 text-muted-foreground">
                Detailed charts coming in next phase.
              </div>
            </CardContent>
          </Card>
          <Card className="col-span-3">
            <CardHeader>
              <CardTitle>Customer Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] flex items-center justify-center border border-dashed rounded-md bg-muted/10 text-muted-foreground">
                Detailed charts coming in next phase.
              </div>
            </CardContent>
          </Card>
      </div>
    </div>
  )
}
