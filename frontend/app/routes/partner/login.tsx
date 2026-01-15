import { Link } from "react-router";
import { LoginForm } from "~/components/login-form";
import { Truck, ArrowLeft } from "lucide-react";
import { ThemeToggle } from "~/components/theme-toggle";

export default function DeliveryPartnerLoginPage() {
  return (
    <div className="flex min-h-svh flex-col bg-gradient-to-b from-background via-background to-muted/20">
      {/* Header */}
      <div className="container flex h-16 items-center gap-4 border-b justify-between">
        <Link to="/" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Home</span>
        </Link>
        <ThemeToggle />
      </div>

      {/* Main Content */}
      <div className="flex flex-1 flex-col items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-5xl">
          {/* Branding Section */}
          <div className="mb-8 text-center space-y-4">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Truck className="h-6 w-6" />
              </div>
              <h1 className="text-3xl font-bold">Delivery Partner Portal</h1>
            </div>
            <p className="text-lg text-muted-foreground">
              Access your delivery assignments, update shipment status, and manage routes
            </p>
          </div>

          <LoginForm user="partner" />
        </div>
      </div>
    </div>
  )
}
