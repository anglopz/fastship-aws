import { Link } from "react-router";
import { Button } from "~/components/ui/button";
import { ThemeToggle } from "~/components/theme-toggle";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-background to-muted/20 py-12 px-4 relative">
      <div className="absolute top-4 right-4">
        <ThemeToggle />
      </div>
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
            Welcome to FastShip
          </h1>
          <p className="text-xl md:text-2xl text-muted-foreground">
            Your trusted partner for fast and reliable shipment management
          </p>
          <p className="text-base text-muted-foreground/80 max-w-xl mx-auto">
            Start your journey with us right now! Manage your shipments efficiently with our comprehensive platform.
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-6">
          <Button asChild size="lg" className="w-full sm:w-auto min-w-[200px]">
            <Link to="/seller/login">Seller Login</Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="w-full sm:w-auto min-w-[200px]">
            <Link to="/partner/login">Delivery Partner Login</Link>
          </Button>
        </div>

        <div className="pt-12 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
          <div className="space-y-2 p-6 rounded-lg border bg-card">
            <h3 className="font-semibold">Fast Delivery</h3>
            <p className="text-sm text-muted-foreground">
              Get your packages delivered quickly and safely
            </p>
          </div>
          <div className="space-y-2 p-6 rounded-lg border bg-card">
            <h3 className="font-semibold">Real-Time Tracking</h3>
            <p className="text-sm text-muted-foreground">
              Track your shipments in real-time from start to finish
            </p>
          </div>
          <div className="space-y-2 p-6 rounded-lg border bg-card">
            <h3 className="font-semibold">Secure Platform</h3>
            <p className="text-sm text-muted-foreground">
              Your data is protected with enterprise-grade security
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
