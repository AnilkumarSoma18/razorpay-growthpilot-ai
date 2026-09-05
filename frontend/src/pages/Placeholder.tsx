
import { Card, CardContent } from "@/components/ui/card"

export function Placeholder({ title, description }: { title: string, description: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[70vh] max-w-2xl mx-auto text-center space-y-6">
      <h1 className="text-4xl font-bold tracking-tight">{title}</h1>
      <p className="text-xl text-muted-foreground">{description}</p>
      <Card className="w-full mt-8 bg-muted/20 border-dashed">
        <CardContent className="pt-6">
          <div className="font-mono text-sm text-muted-foreground">
            This module is scheduled for implementation in a future buildathon phase.
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
