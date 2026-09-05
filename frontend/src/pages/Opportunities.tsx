
import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { fetchOpportunities, runGrowthAgent, Opportunity } from "@/api/growth"
import { requestApproval } from "@/api/approvals"
import { getDemoMerchantId } from "@/api/analytics"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"

export function Opportunities() {
  const queryClient = useQueryClient()
  const [isAgentRunning, setIsAgentRunning] = useState(false)

  const { data: merchantId } = useQuery({ queryKey: ['demoMerchant'], queryFn: getDemoMerchantId })

  const { data: opportunities, isLoading } = useQuery({
    queryKey: ['opportunities', merchantId],
    queryFn: () => fetchOpportunities(merchantId!),
    enabled: !!merchantId
  })

  const runAgentMutation = useMutation({
    mutationFn: () => runGrowthAgent(merchantId!, new Date().getTime().toString()),
    onMutate: () => setIsAgentRunning(true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
      queryClient.invalidateQueries({ queryKey: ['agentRuns'] })
      setIsAgentRunning(false)
    },
    onError: () => setIsAgentRunning(false)
  })

  const requestApprovalMutation = useMutation({
    mutationFn: (oppId: string) => requestApproval(merchantId!, oppId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['opportunities'] })
      queryClient.invalidateQueries({ queryKey: ['approvals'] })
    }
  })

  if (isLoading) return <div className="p-8 text-center text-muted-foreground animate-pulse">Loading opportunities...</div>

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">Revenue Opportunities</h1>
        <button 
          onClick={() => runAgentMutation.mutate()}
          disabled={isAgentRunning || !merchantId}
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md font-medium text-sm disabled:opacity-50"
        >
          {isAgentRunning ? "Analyzing merchant data..." : "Run Growth Analysis"}
        </button>
      </div>
      
      {(!opportunities || opportunities.length === 0) && !isAgentRunning ? (
        <Card className="w-full mt-8 bg-muted/20 border-dashed">
            <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-4">
                <div className="font-mono text-sm text-muted-foreground">Growth opportunity engine is idle. No opportunities found.</div>
            </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6">
        {opportunities?.map((opp: Opportunity) => (
          <Card key={opp.id} className="border-l-4 border-l-primary shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-xs font-bold text-primary mb-1 uppercase tracking-wider">{opp.type.replace(/_/g, ' ')}</div>
                  <CardTitle className="text-xl">{opp.title}</CardTitle>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">{opp.score.toFixed(0)}</div>
                  <div className="text-xs font-mono text-muted-foreground">RULE-BASED SCORE</div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="mb-4">{opp.description}</p>
              
              <div className="grid md:grid-cols-2 gap-4 bg-muted/30 p-4 rounded-md border border-muted">
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-muted-foreground">OBSERVED EVIDENCE</h4>
                  <ul className="text-sm space-y-1">
                    {Object.entries(opp.evidence).map(([k, v]) => {
                        if (k === 'score_components' || k === 'impact_estimate_status' || k === 'approval_status' || k === 'approval_id') return null;
                        return <li key={k}><span className="font-mono text-xs text-muted-foreground">{k}:</span> <span className="font-medium">{String(v)}</span></li>
                    })}
                  </ul>
                  {opp.evidence.score_components && (
                      <div className="mt-3 text-xs border-t pt-2">
                        <span className="font-mono text-muted-foreground">Score Formula: </span>
                        Strength({opp.evidence.score_components.evidence_strength}) + 
                        Relevance({opp.evidence.score_components.population_relevance}) + 
                        Value({opp.evidence.score_components.business_value_signal}) + 
                        Conf({opp.evidence.score_components.confidence}) - 
                        Risk({opp.evidence.score_components.risk_penalty})
                      </div>
                  )}
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-muted-foreground">PREDICTED IMPACT</h4>
                  <div className="text-sm space-y-2">
                    <div className="inline-block px-2 py-1 bg-amber-100 text-amber-800 text-xs font-bold rounded">
                        {opp.prediction_status || "UNAVAILABLE"}
                    </div>
                    <p className="text-xs text-muted-foreground">
                        Predictive model has not yet been trained. Using deterministic strategy fallback.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="bg-muted/10 border-t pt-4 flex justify-between items-center">
                <div className="text-sm font-medium">
                    <span className="text-muted-foreground">Strategy: </span> 
                    {opp.recommended_action}
                </div>
                {opp.requires_approval && (
                    <div className="text-xs font-bold">
                        {!opp.evidence.approval_status && (
                            <button 
                                onClick={() => requestApprovalMutation.mutate(opp.id)}
                                disabled={requestApprovalMutation.isPending}
                                className="bg-blue-600 text-white px-3 py-1.5 rounded text-xs hover:bg-blue-700 disabled:opacity-50"
                            >
                                REQUEST APPROVAL
                            </button>
                        )}
                        {opp.evidence.approval_status === 'PENDING' && <span className="px-2 py-1 bg-amber-100 text-amber-800 rounded">APPROVAL PENDING</span>}
                        {opp.evidence.approval_status === 'APPROVED' && <span className="px-2 py-1 bg-green-100 text-green-800 rounded">APPROVED — READY FOR EXECUTION</span>}
                        {opp.evidence.approval_status === 'REJECTED' && <span className="px-2 py-1 bg-red-100 text-red-800 rounded">REJECTED</span>}
                    </div>
                )}
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  )
}
