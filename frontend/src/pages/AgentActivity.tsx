
import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { fetchAgentRuns, fetchRunActions } from "@/api/growth"
import { getDemoMerchantId } from "@/api/analytics"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

function RunTimeline({ runId }: { runId: string }) {
    const { data: actions, isLoading } = useQuery({
        queryKey: ['agentActions', runId],
        queryFn: () => fetchRunActions(runId)
    })

    if (isLoading) return <div className="text-xs p-4 animate-pulse">Loading trace...</div>
    if (!actions?.length) return <div className="text-xs p-4">No operational trace found.</div>

    return (
        <div className="mt-4 space-y-4 pl-4 border-l-2 border-muted">
            {actions.map(action => (
                <div key={action.id} className="relative">
                    <div className="absolute -left-[21px] top-1 w-3 h-3 bg-primary rounded-full ring-4 ring-background" />
                    <div className="text-sm font-semibold">{action.step}</div>
                    <div className="text-xs text-muted-foreground mb-1">{new Date(action.created_at).toLocaleString()}</div>
                    <div className="text-xs p-2 bg-muted rounded-md font-mono">
                        <div><span className="text-muted-foreground">Tool:</span> {action.tool_name}</div>
                        <div><span className="text-muted-foreground">Summary:</span> {action.output_summary}</div>
                    </div>
                </div>
            ))}
        </div>
    )
}

export function AgentActivity() {
  const { data: merchantId } = useQuery({
    queryKey: ['demoMerchant'],
    queryFn: getDemoMerchantId
  })

  const { data: runs, isLoading } = useQuery({
    queryKey: ['agentRuns', merchantId],
    queryFn: () => fetchAgentRuns(merchantId!),
    enabled: !!merchantId
  })

  const [expandedRun, setExpandedRun] = useState<string | null>(null)

  if (isLoading) return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading agent runs...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Agent Activity Trace</h1>
      </div>
      
      {(!runs || runs.length === 0) ? (
        <Card className="w-full mt-8 bg-muted/20 border-dashed">
            <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="font-mono text-sm text-muted-foreground">
                    No agent runs found in the audit log.
                </div>
            </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4">
        {runs?.map(run => (
          <Card key={run.run_id} className="cursor-pointer hover:bg-muted/10 transition-colors" onClick={() => setExpandedRun(expandedRun === run.run_id ? null : run.run_id)}>
            <CardHeader className="py-4">
              <div className="flex justify-between items-center">
                <div>
                  <CardTitle className="text-lg font-mono text-primary">{run.run_id.split('-')[0]}... (MERCHANT_GROWTH)</CardTitle>
                  <div className="text-sm text-muted-foreground mt-1">Started: {new Date(run.started_at).toLocaleString()}</div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-bold px-2 py-1 rounded ${run.status === 'COMPLETED' ? 'bg-green-100 text-green-800' : run.status === 'FAILED' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800'}`}>
                    {run.status}
                  </div>
                </div>
              </div>
            </CardHeader>
            {expandedRun === run.run_id && (
                <CardContent className="border-t pt-4">
                    <div className="text-sm font-medium mb-2 text-primary">{run.output_summary}</div>
                    <RunTimeline runId={run.run_id} />
                </CardContent>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
