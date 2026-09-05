
import { useState } from "react"

import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { apiClient } from "@/api/client"

export function Checkout() {
  const [status, setStatus] = useState<"CART" | "VERIFYING" | "SUCCESS" | "FAILED" | "PENDING">("CART")
  
  // Dummy internal order ID for demo
  const internalOrderId = "11111111-1111-1111-1111-111111111111"

  const handlePayment = async () => {
    try {
      // 1. Create Razorpay Test Order
      const { data: orderData } = await apiClient.post("/api/payments/razorpay/order", {
        internal_order_id: internalOrderId
      })

      // 2. Mock Razorpay Checkout (Since we don't load external JS in this isolated test)
      // In a real env, we would do:
      // const rzp = new window.Razorpay(options); rzp.open();
      // For this buildathon UI, we simulate the frontend callback logic.
      
      const mockCallback = {
          razorpay_payment_id: "pay_mock123",
          razorpay_order_id: orderData.razorpay_order_id,
          razorpay_signature: "valid_mock"
      };

      setStatus("VERIFYING")

      // 3. Verify Payment
      const { data: verifyData } = await apiClient.post("/api/payments/razorpay/verify", mockCallback)
      
      if (verifyData.status === "PAYMENT_PENDING") {
          setStatus("PENDING")
      } else {
          setStatus("SUCCESS")
      }
      
    } catch (err: any) {
        setStatus("FAILED")
    }
  }

  return (
    <div className="space-y-6 max-w-2xl mx-auto mt-12">
      <div className="bg-amber-100 text-amber-900 px-4 py-2 text-center text-sm font-bold border border-amber-300 rounded">
        RAZORPAY TEST MODE - No real money is involved
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Secure Checkout</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
            {status === "CART" && (
                <>
                    <div className="flex justify-between py-2 border-b">
                        <span>Demo Product Name</span>
                        <span>₹100.50</span>
                    </div>
                    <div className="flex justify-between py-2 font-bold">
                        <span>Total</span>
                        <span>₹100.50</span>
                    </div>
                </>
            )}
            
            {status === "VERIFYING" && (
                <div className="text-center py-8 text-muted-foreground animate-pulse font-mono">
                    VERIFYING PAYMENT...
                </div>
            )}
            
            {status === "PENDING" && (
                <div className="text-center py-8 text-blue-600 font-bold border rounded bg-blue-50">
                    PAYMENT PENDING<br/><span className="text-sm font-normal text-blue-800">Your payment is being verified with Razorpay. Awaiting webhook capture.</span>
                </div>
            )}
            
            {status === "SUCCESS" && (
                <div className="text-center py-8 text-green-600 font-bold border rounded bg-green-50">
                    PAYMENT SUCCESSFUL<br/><span className="text-sm font-normal text-green-800">Internal order updated safely via backend webhook.</span>
                </div>
            )}
            
            {status === "FAILED" && (
                <div className="text-center py-8 text-red-600 font-bold border rounded bg-red-50">
                    PAYMENT FAILED<br/><span className="text-sm font-normal text-red-800">Verification rejected. No success recorded.</span>
                </div>
            )}
        </CardContent>
        <CardFooter className="flex justify-end bg-muted/10">
            {status === "CART" && (
                <button 
                    onClick={handlePayment}
                    className="bg-primary text-primary-foreground px-6 py-2 rounded font-bold"
                >Pay Now</button>
            )}
        </CardFooter>
      </Card>
    </div>
  )
}
