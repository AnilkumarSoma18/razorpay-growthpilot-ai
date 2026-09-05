
import { useState, useRef, useEffect } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { apiClient } from "@/api/client"
import { getDemoMerchantId } from "@/api/analytics"
import { useNavigate } from "react-router-dom"

export function Shopping() {
  const navigate = useNavigate()
  
  const { data: merchantId } = useQuery({ queryKey: ['demoMerchant'], queryFn: getDemoMerchantId })
  
  const [sessionId] = useState("session_" + Math.random().toString(36).substring(7))
  const [messages, setMessages] = useState<{role: "user"|"assistant", content: string, products?: any[]}[]>([
      { role: "assistant", content: "Hi! I'm your AI Shopping Assistant. How can I help you today?" }
  ])
  const [input, setInput] = useState("")
  
  const { data: cartData, refetch: refetchCart } = useQuery({
      queryKey: ['cart', sessionId],
      queryFn: async () => {
          if (!merchantId) return { items: [], total: 0 }
          const { data } = await apiClient.get(`/api/shopping/cart?merchant_id=${merchantId}&session_id=${sessionId}`)
          return data
      },
      enabled: !!merchantId
  })

  const chatMutation = useMutation({
      mutationFn: async (msg: string) => {
          const { data } = await apiClient.post('/api/shopping/chat', {
              merchant_id: merchantId,
              session_id: sessionId,
              message: msg
          })
          return data
      },
      onSuccess: (data) => {
          setMessages(prev => [...prev, { role: "assistant", content: data.response, products: data.products }])
      }
  })

  const actionMutation = useMutation({
      mutationFn: async ({ productId, action }: { productId: string, action: string }) => {
          const { data } = await apiClient.post('/api/shopping/action', {
              merchant_id: merchantId,
              session_id: sessionId,
              product_id: productId,
              action
          })
          return data
      },
      onSuccess: (_, variables) => {
          if (variables.action === "add_to_cart") {
              refetchCart()
          } else if (variables.action === "checkout") {
              // Redirect to checkout with internal_order_id, but here we can just navigate
              navigate("/checkout")
          }
      }
  })

  const handleSend = () => {
      if (!input.trim() || !merchantId) return
      setMessages(prev => [...prev, { role: "user", content: input }])
      chatMutation.mutate(input)
      setInput("")
  }

  const handleCheckout = async () => {
      if (!merchantId) return
      try {
          await apiClient.post('/api/shopping/action', {
              merchant_id: merchantId,
              session_id: sessionId,
              product_id: "00000000-0000-0000-0000-000000000000", // Dummy UUID for checkout since it operates on cart
              action: "checkout"
          })
          navigate("/checkout")
      } catch (e: any) {
          alert("Checkout failed: " + (e?.response?.data?.detail || e.message))
      }
  }

  const messagesEndRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  return (
    <div className="grid md:grid-cols-3 gap-6 h-[85vh]">
      {/* Left Chat Window */}
      <Card className="md:col-span-2 flex flex-col h-full shadow-sm">
        <CardHeader className="border-b bg-muted/20 py-3">
          <CardTitle className="text-lg flex justify-between items-center">
              <span>AI Shopping Assistant</span>
              <span className="text-xs bg-amber-100 text-amber-900 px-2 py-1 rounded font-mono font-bold">SYNTHETIC DATA DEMO</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((m, i) => (
                <div key={i} className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                    <div className={`px-4 py-2 rounded-xl max-w-[80%] ${m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                        {m.content}
                    </div>
                    {m.products && m.products.length > 0 && (
                        <div className="grid sm:grid-cols-2 gap-4 mt-4 w-full">
                            {m.products.map((p: any) => (
                                <Card key={p.id} className="shadow-sm border border-border/50">
                                    <CardContent className="p-4">
                                        <h4 className="font-bold text-sm truncate">{p.name}</h4>
                                        <div className="text-primary font-mono text-sm mt-1">₹{p.price}</div>
                                        <div className="text-xs text-muted-foreground mt-2 italic bg-blue-50 text-blue-800 p-2 rounded">
                                            <strong>WHY THIS PRODUCT?</strong><br/>
                                            {p.reason}
                                        </div>
                                    </CardContent>
                                    <CardFooter className="p-4 pt-0">
                                        <button 
                                            onClick={() => actionMutation.mutate({ productId: p.id, action: "add_to_cart" })}
                                            className="w-full bg-secondary text-secondary-foreground py-2 rounded text-xs font-bold hover:bg-secondary/80 transition-colors"
                                            disabled={actionMutation.isPending}
                                        >
                                            {actionMutation.isPending && actionMutation.variables?.productId === p.id ? "Adding..." : "Add to Cart"}
                                        </button>
                                    </CardFooter>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            ))}
            {chatMutation.isPending && (
                <div className="flex items-start">
                    <div className="px-4 py-2 rounded-xl bg-muted animate-pulse">Thinking...</div>
                </div>
            )}
            <div ref={messagesEndRef} />
        </CardContent>
        <CardFooter className="border-t p-4">
            <div className="flex w-full space-x-2">
                <input 
                    type="text" 
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="E.g. I need headphones under ₹3000..." 
                    className="flex-1 border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                    disabled={chatMutation.isPending}
                />
                <button 
                    onClick={handleSend}
                    disabled={chatMutation.isPending || !input.trim()}
                    className="bg-primary text-primary-foreground px-4 py-2 rounded font-bold text-sm"
                >Send</button>
            </div>
        </CardFooter>
      </Card>

      {/* Right Cart Sidebar */}
      <Card className="flex flex-col h-full shadow-sm bg-muted/10">
        <CardHeader className="border-b py-3">
            <CardTitle className="text-lg">Your Cart</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
            {!cartData || cartData.items.length === 0 ? (
                <div className="text-center text-muted-foreground text-sm py-12">
                    Your cart is empty.
                </div>
            ) : (
                <div className="space-y-4">
                    {cartData.items.map((item: any) => (
                        <div key={item.id} className="flex justify-between items-center bg-background p-3 rounded border text-sm">
                            <div className="flex-1 min-w-0 pr-4">
                                <p className="font-bold truncate">{item.name}</p>
                                <p className="text-muted-foreground">Qty: {item.quantity} × ₹{item.price}</p>
                            </div>
                            <div className="font-mono font-bold">
                                ₹{item.subtotal}
                            </div>
                        </div>
                    ))}
                    
                    <div className="border-t pt-4 flex justify-between items-center font-bold text-lg">
                        <span>Total</span>
                        <span>₹{cartData.total}</span>
                    </div>
                </div>
            )}
        </CardContent>
        <CardFooter className="border-t p-4">
            <button 
                onClick={handleCheckout}
                disabled={!cartData || cartData.items.length === 0}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3 rounded font-bold transition-colors disabled:opacity-50"
            >
                Proceed to Checkout
            </button>
        </CardFooter>
      </Card>
    </div>
  )
}
