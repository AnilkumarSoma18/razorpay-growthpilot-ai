
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AppLayout } from "./components/layout/AppLayout"
import { CommandCenter } from "./pages/CommandCenter"
import { Dashboard } from "./pages/Dashboard"
import { Opportunities } from "./pages/Opportunities"
import { AgentActivity } from "./pages/AgentActivity"
import { Approvals } from "./pages/Approvals"
import { Simulator } from "./pages/Simulator"
import { AuditTrail } from "./pages/AuditTrail"
import { Checkout } from "./pages/Checkout"
import { Shopping } from "./pages/Shopping"
import { Placeholder } from "./pages/Placeholder"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<CommandCenter />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/opportunities" element={<Opportunities />} />
          <Route path="/simulator" element={<Simulator />} />
          <Route path="/approvals" element={<Approvals />} />
          <Route path="/products" element={<Placeholder title="Products" description="Catalog management coming soon." />} />
          <Route path="/customers" element={<Placeholder title="Customers" description="Customer segment analytics coming soon." />} />
          <Route path="/shopping" element={<Shopping />} />
          <Route path="/checkout" element={<Checkout />} />
          <Route path="/experiments" element={<Placeholder title="Experiments" description="A/B testing and agent strategies coming soon." />} />
          <Route path="/agent-activity" element={<AgentActivity />} />
          <Route path="/audit" element={<AuditTrail />} />
          <Route path="/settings" element={<Placeholder title="Settings" description="Store configuration coming soon." />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
