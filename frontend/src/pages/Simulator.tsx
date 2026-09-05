

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { runSimulation, executeStrategy } from "@/api/execution"
import { fetchApprovals } from "@/api/approvals"
import { getDemoMerchantId } from "@/api/analytics"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"

export function Simulator() {
  const queryClient = useQueryClient()
  const { data: merchantId } = useQuery({ queryKey: ['demoMerchant'], queryFn: getDemoMerchantId })

  const { data: approvals, isLoading } = useQuery({
    queryKey: ['approvals', merchantId],
    queryFn: () => fetchApprovals(merchantId!),
    enabled: !!merchantId
  })

  const simulateMutation = useMutation({
    mutationFn: (oppId: string) => runSimulation(merchantId!, oppId)
  })

  const executeMutation = useMutation({
    mutationFn: ({oppId, appId}: {oppId: string, appId: string}) => executeStrategy(merchantId!, oppId, appId, new Date().getTime().toString()),
    onSuccess: () => {
        alert("SIMULATED EXECUTION COMPLETE\nVerified and audited.");
        queryClient.invalidateQueries({ queryKey: ['opportunities'] })
        queryClient.invalidateQueries({ queryKey: ['approvals'] })
        queryClient.invalidateQueries({ queryKey: ['auditLogs'] })
    },
    onError: (err: any) => {
        alert(`EXECUTION FAILED: ${err?.response?.data?.detail || err.message}`);
    }
  })

  if (isLoading) return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading simulator environment...</div>

  const approvedStrategies = approvals?.filter(a => a.status === 'APPROVED') || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Growth Simulator (Demo Environment)</h1>
      </div>
      
      {approvedStrategies.length === 0 ? (
        <Card className="w-full mt-8 bg-muted/20 border-dashed">
            <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="font-mono text-sm text-muted-foreground">No APPROVED strategies ready for simulation. Please approve a strategy in the Approval Center first.</div>
            </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6">
        {approvedStrategies.map(app => (
          <Card key={app.id} className="border-l-4 border-l-blue-500 shadow-sm">
            <CardHeader className="pb-3 border-b">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-xs font-bold text-blue-600 mb-1 uppercase tracking-wider">AUTHORIZED FOR SIMULATED EXECUTION</div>
                  <CardTitle className="text-xl">{app.evidence_snapshot?.opportunity_title}</CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
                {!simulateMutation.data || simulateMutation.variables !== app.opportunity_id ? (
                    <div className="text-center py-8 border border-dashed rounded bg-muted/10">
                        <button 
                            onClick={() => simulateMutation.mutate(app.opportunity_id)}
                            className="bg-primary text-primary-foreground px-6 py-3 rounded-md font-bold"
                        >RUN SIMULATION</button>
                    </div>
                ) : (
                    <div className="space-y-6">
                        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded text-sm text-amber-900">
                            <strong>PREDICTION UNAVAILABLE:</strong> The ML predictive model is not yet trained. 
                            This simulation uses deterministic historical fallbacks. NO CAUSAL LIFT IS CLAIMED.
                        </div>
                        
                        <div className="grid md:grid-cols-2 gap-6">
                            <div className="bg-muted/30 p-4 rounded border">
                                <h4 className="font-bold text-sm text-muted-foreground mb-4">OBSERVED BASELINE</h4>
                                <ul className="space-y-2 text-sm font-mono">
                                    {Object.entries(simulateMutation.data.baseline_metrics).map(([k, v]) => (
                                        <li key={k} className="flex justify-between"><span>{k}</span> <strong>{String(v)}</strong></li>
                                    ))}
                                </ul>
                            </div>
                            <div className="bg-blue-50 p-4 rounded border border-blue-100">
                                <h4 className="font-bold text-sm text-blue-800 mb-4 flex items-center justify-between">
                                    <span>SIMULATED RESULT</span>
                                    <span className="bg-blue-200 text-blue-800 text-xs px-2 py-1 rounded">SIMULATED ONLY</span>
                                </h4>
                                <ul className="space-y-2 text-sm font-mono text-blue-900">
                                    {Object.entries(simulateMutation.data.simulated_metrics).map(([k, v]) => (
                                        <li key={k} className="flex justify-between"><span>{k}</span> <strong>{String(v)}</strong></li>
                                    ))}
                                </ul>
                            </div>
                        </div>

                        <div className="bg-muted p-4 rounded text-xs font-mono">
                            <strong>SIMULATION ASSUMPTIONS:</strong>
                            <ul className="list-disc pl-4 mt-2 space-y-1">
                                {simulateMutation.data.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                            </ul>
                        </div>
                    </div>
                )}
            </CardContent>
            <CardFooter className="bg-muted/10 border-t pt-4 flex justify-between items-center">
                <div className="text-xs text-muted-foreground max-w-xl">
                    This will perform a simulated operation only. No real customer communication, payment, pricing, or Razorpay transaction will occur.
                </div>
                <button 
                    onClick={() => {
                        if (confirm("Confirm execution of this SIMULATED ONLY action. No real transactions will occur.")) {
                            executeMutation.mutate({ oppId: app.opportunity_id, appId: app.id })
                        }
                    }}
                    disabled={executeMutation.isPending}
                    className="bg-green-600 text-white px-4 py-2 rounded-md font-bold text-sm hover:bg-green-700 disabled:opacity-50"
                >
                    {executeMutation.isPending ? "EXECUTING..." : "EXECUTE DEMO ACTION"}
                </button>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
