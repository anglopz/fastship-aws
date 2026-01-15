import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { useContext } from "react"
import { Link } from "react-router"
import { AuthContext, type UserType } from "~/contexts/AuthContext"
import { Mail, Lock, LogIn } from "lucide-react"

export function LoginForm({
  className,
  user,
  ...props
}: { user: UserType } & React.ComponentProps<"div">) {

  const { login } = useContext(AuthContext)

  const userLabel = user === "seller" ? "Seller" : "Delivery Partner"
  const features = user === "seller" 
    ? [
        "Track all your shipments in one place",
        "Get real-time delivery updates",
        "Manage your business efficiently"
      ]
    : [
        "View assigned delivery routes",
        "Update shipment status on the go",
        "Access delivery history and earnings"
      ]

  function loginUser(data: FormData) {
    const email = data.get("email")
    const password = data.get("password")

    if (!email || !password) {
      return
    }

    login(user, email.toString(), password.toString())
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden shadow-lg border-2">
        <CardContent className="grid p-0 md:grid-cols-2">
          {/* Login Form */}
          <div className="p-8 md:p-10 flex flex-col justify-center">
            <CardHeader className="px-0 pb-6">
              <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
              <CardDescription className="text-base">
                Sign in to your {userLabel} account to continue
              </CardDescription>
            </CardHeader>
            
            <form onSubmit={(e) => { e.preventDefault(); loginUser(new FormData(e.currentTarget)); }} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email Address
                </Label>
                <Input
                  id="email"
                  type="email"
                  name="email"
                  placeholder="you@example.com"
                  required
                  className="h-11"
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                    <Lock className="h-4 w-4" />
                    Password
                  </Label>
                  <Link
                    to={`/${user}/forgot-password`}
                    className="text-sm text-primary hover:underline underline-offset-2"
                  >
                    Forgot password?
                  </Link>
                </div>
                <Input 
                  id="password" 
                  type="password" 
                  name="password" 
                  placeholder="Enter your password"
                  required 
                  className="h-11"
                />
              </div>
              
              <Button type="submit" className="w-full h-11 text-base font-semibold" size="lg">
                <LogIn className="mr-2 h-4 w-4" />
                Sign In
              </Button>
              
              <div className="text-center text-sm text-muted-foreground pt-2">
                Don&apos;t have an account?{" "}
                <Link to="#" className="text-primary font-medium hover:underline underline-offset-2">
                  Contact support to register
                </Link>
              </div>
            </form>
          </div>

          {/* Feature Panel */}
          <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-background border-l p-8 md:p-10 flex flex-col justify-center space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Why use FastShip?</h3>
              <ul className="space-y-4">
                {features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-semibold mt-0.5">
                      {index + 1}
                    </div>
                    <span className="text-sm text-muted-foreground">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="pt-4 border-t">
              <p className="text-xs text-muted-foreground leading-relaxed">
                By signing in, you agree to our{" "}
                <Link to="#" className="text-primary hover:underline underline-offset-2">Terms of Service</Link>
                {" "}and{" "}
                <Link to="#" className="text-primary hover:underline underline-offset-2">Privacy Policy</Link>.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
