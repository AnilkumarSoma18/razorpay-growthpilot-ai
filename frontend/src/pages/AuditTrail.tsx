
import { useQuery } from "@tanstack/react-query"
import { fetchAuditLogs } from "@/api/execution"
import { getDemoMerchantId } from "@/api/analytics"
import { Card, CardContent } from "@/components/ui/card"

export function AuditTrail() {
  const { data: merchantId } = useQuery({ queryKey: ['demoMerchant'], queryFn: getDemoMerchantId })

  const { data: logs, isLoading } = useQuery({
    queryKey: ['auditLogs', merchantId],
    queryFn: () => fetchAuditLogs(merchantId!),
    enabled: !!merchantId
  })

  if (isLoading) return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading audit trail...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Governance Audit Trail</h1>
      
      {(!logs || logs.length === 0) ? (
        <Card className="w-full mt-8 bg-muted/20 border-dashed">
            <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="font-mono text-sm text-muted-foreground">No audit logs found.</div>
            </CardContent>
        </Card>
      ) : null}

      <div className="bg-card border rounded-md shadow-sm overflow-hidden">
        <table className="w-full text-sm text-left">
            <thead className="bg-muted/50 text-muted-foreground text-xs uppercase font-mono">
                <tr>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Actor</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Details</th>
                </tr>
            </thead>
            <tbody className="divide-y">
                {logs?.map(log => (
                    <tr key={log.id} className="hover:bg-muted/30">
                        <td className="px-4 py-3 whitespace-nowrap text-xs text-muted-foreground">{new Date(log.timestamp).toLocaleString()}</td>
                        <td className="px-4 py-3 font-medium">{log.actor}</td>
                        <td className="px-4 py-3 font-bold text-primary">{log.action}</td>
                        <td className="px-4 py-3">
                            <span className={`px-2 py-1 text-xs font-bold rounded ${log.status === 'SUCCESS' ? 'bg-green-100 text-green-800' : log.status === 'FAILED' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
                                {log.status}
                            </span>
                        </td>
                        <td className="px-4 py-3 text-xs">{log.summary}</td>
                    </tr>
                ))}
            </tbody>
        </table>
      </div>
    </div>
  )
}
