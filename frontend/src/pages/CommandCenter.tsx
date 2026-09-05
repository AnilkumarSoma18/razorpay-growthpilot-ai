
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Link } from "react-router-dom"

export function CommandCenter() {
  return (
    <div className="space-y-8 max-w-5xl mx-auto py-8">
      <div>
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">GrowthPilot AI Command Center</h1>
        <p className="text-xl text-muted-foreground">Autonomous Merchant Growth & Agentic Commerce Engine</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-primary/50 shadow-md">
          <CardHeader>
            <CardTitle className="text-xl text-primary flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-green-500 inline-block"></span>
              Analytics Engine
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4">Real-time processing of merchant synthetic data, revenue, conversion rates, and AOV.</p>
            <div className="text-sm bg-muted p-3 rounded-md mb-4 font-mono">Status: Connected to Database</div>
            <Link to="/dashboard" className="text-primary hover:underline font-medium">View Dashboard &rarr;</Link>
          </CardContent>
        </Card>

        <Card className="border-dashed bg-muted/30">
          <CardHeader>
            <CardTitle className="text-xl text-muted-foreground flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-muted-foreground inline-block"></span>
              Growth Opportunity Engine
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-muted-foreground">Analyzing merchant performance and identifying revenue opportunities.</p>
            <div className="text-sm bg-muted/50 p-3 rounded-md mb-4 font-mono text-muted-foreground">Status: Coming in next phase</div>
          </CardContent>
        </Card>

        <Card className="border-dashed bg-muted/30">
          <CardHeader>
            <CardTitle className="text-xl text-muted-foreground flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-muted-foreground inline-block"></span>
              Agent Engine (LangGraph)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-muted-foreground">Agentic workflow orchestration, tool execution, and guardrails.</p>
            <div className="text-sm bg-muted/50 p-3 rounded-md mb-4 font-mono text-muted-foreground">Status: Coming in next phase</div>
          </CardContent>
        </Card>

        <Card className="border-dashed bg-muted/30">
          <CardHeader>
            <CardTitle className="text-xl text-muted-foreground flex items-center gap-2">
              <span className="h-3 w-3 rounded-full bg-muted-foreground inline-block"></span>
              Razorpay Integration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-muted-foreground">TEST MODE checkouts, webhook verification, and automated refunds.</p>
            <div className="text-sm bg-muted/50 p-3 rounded-md mb-4 font-mono text-muted-foreground">Status: Coming in next phase</div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
