
import { Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"
import { 
    LayoutDashboard, 
    Lightbulb, 
    BarChart3, 
    CheckSquare, 
    Box, 
    Users, 
    MessageSquare, 
    FlaskConical, 
    Activity, 
    FileText, 
    Settings 
} from "lucide-react"

const navItems = [
  { name: "Command Center", path: "/", icon: Activity },
  { name: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { name: "Revenue Opportunities", path: "/opportunities", icon: Lightbulb },
  { name: "Growth Simulator", path: "/simulator", icon: BarChart3 },
  { name: "Approvals", path: "/approvals", icon: CheckSquare },
  { name: "Products", path: "/products", icon: Box },
  { name: "Customers", path: "/customers", icon: Users },
  { name: "AI Shopping", path: "/shopping", icon: MessageSquare },
  { name: "Experiments", path: "/experiments", icon: FlaskConical },
  { name: "Agent Activity", path: "/agent-activity", icon: Activity },
  { name: "Audit Trail", path: "/audit", icon: FileText },
  { name: "Settings", path: "/settings", icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  
  return (
    <div className="flex h-full w-64 flex-col border-r bg-background">
      <div className="flex h-14 items-center border-b px-4">
        <span className="font-bold text-lg text-primary">GrowthPilot AI</span>
      </div>
      <div className="flex-1 overflow-y-auto py-4">
        <nav className="grid gap-1 px-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:text-primary",
                  isActive ? "bg-muted text-primary" : "text-muted-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
