
import { useQuery } from "@tanstack/react-query"
import { fetchHealth } from "@/api/analytics"
import { Bell, User } from "lucide-react"

export function TopBar() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30000
  })

  const isConnected = health?.status === "ok"

  return (
    <header className="flex h-14 items-center gap-4 border-b bg-background px-6">
      <div className="flex-1 font-semibold text-lg">Razorpay GrowthPilot AI</div>
      
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium bg-amber-50 text-amber-600 border-amber-200">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
          </span>
          DEMO ENVIRONMENT / SYNTHETIC DATA
        </div>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>Backend</span>
          {isConnected ? (
            <span className="flex items-center text-green-600"><span className="mr-1 h-2 w-2 rounded-full bg-green-600"></span> Connected</span>
          ) : (
            <span className="flex items-center text-red-600"><span className="mr-1 h-2 w-2 rounded-full bg-red-600"></span> Unavailable</span>
          )}
        </div>
        
        <button className="text-muted-foreground hover:text-foreground">
          <Bell className="h-5 w-5" />
        </button>
        <button className="h-8 w-8 rounded-full bg-muted flex items-center justify-center">
          <User className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
