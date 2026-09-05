
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchApprovals, approveRequest, rejectRequest, Approval } from "@/api/approvals"
import { getDemoMerchantId } from "@/api/analytics"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"

export function Approvals() {
  const queryClient = useQueryClient()
  const { data: merchantId } = useQuery({ queryKey: ['demoMerchant'], queryFn: getDemoMerchantId })

  const { data: approvals, isLoading } = useQuery({
    queryKey: ['approvals', merchantId],
    queryFn: () => fetchApprovals(merchantId!),
    enabled: !!merchantId
  })

  const approveMutation = useMutation({
    mutationFn: (id: string) => approveRequest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
    }
  })

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string, reason: string }) => rejectRequest(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
    }
  })

  if (isLoading) return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading approvals...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold tracking-tight">Approval Center</h1>
      
      {(!approvals || approvals.length === 0) ? (
        <Card className="w-full mt-8 bg-muted/20 border-dashed">
            <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="font-mono text-sm text-muted-foreground">No pending approvals found.</div>
            </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6">
        {approvals?.map((app: Approval) => (
          <Card key={app.id} className={`border-l-4 ${app.status === 'PENDING' ? 'border-l-amber-500' : app.status === 'APPROVED' ? 'border-l-green-500' : 'border-l-red-500'} shadow-sm`}>
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className={`text-xs font-bold mb-1 uppercase tracking-wider ${app.status === 'PENDING' ? 'text-amber-600' : app.status === 'APPROVED' ? 'text-green-600' : 'text-red-600'}`}>{app.status}</div>
                  <CardTitle className="text-xl">{app.evidence_snapshot?.opportunity_title || "Unknown Opportunity"}</CardTitle>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">{app.evidence_snapshot?.rule_based_score}</div>
                  <div className="text-xs font-mono text-muted-foreground">RULE-BASED SCORE</div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="mb-4">{app.reason}</p>
              <div className="grid md:grid-cols-2 gap-4 bg-muted/30 p-4 rounded-md border border-muted">
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-muted-foreground">STRATEGY</h4>
                  <div className="text-sm font-medium">{app.action_description}</div>
                  <div className="mt-3 text-xs border-t pt-2 space-y-1">
                    <span className="font-mono text-muted-foreground block mb-1">Constraints:</span>
                    {app.evidence_snapshot?.constraints?.map((c: string, i: number) => (
                        <div key={i} className="text-amber-700">- {c}</div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-muted-foreground">IMPACT & RISK</h4>
                  <div className="text-sm space-y-2">
                    <div>Risk Level: <span className="font-medium">{app.risk}</span></div>
                    <div className="inline-block px-2 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded">
                        {app.evidence_snapshot?.prediction_status || "UNAVAILABLE"}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="bg-muted/10 border-t pt-4 flex gap-4">
                {app.status === 'PENDING' ? (
                    <>
                        <button 
                            onClick={() => { if(confirm("Authorize this strategy for future execution?")) approveMutation.mutate(app.id) }} 
                            className="bg-green-600 text-white px-4 py-2 rounded-md font-medium text-sm hover:bg-green-700"
                        >APPROVE</button>
                        <button 
                            onClick={() => { const reason = prompt("Rejection reason:"); if(reason) rejectMutation.mutate({id: app.id, reason}) }} 
                            className="bg-red-600 text-white px-4 py-2 rounded-md font-medium text-sm hover:bg-red-700"
                        >REJECT</button>
                    </>
                ) : app.status === 'APPROVED' ? (
                    <div className="text-sm font-bold text-green-700">AUTHORIZED FOR FUTURE EXECUTION</div>
                ) : (
                    <div className="text-sm font-bold text-red-700">REJECTED</div>
                )}
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
