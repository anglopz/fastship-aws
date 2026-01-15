import { cn } from "~/lib/utils"
import { Button } from "~/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card"
import { Input } from "~/components/ui/input"
import { Label } from "~/components/ui/label"
import { Link } from "react-router"
import { type UserType } from "~/contexts/AuthContext"
import api from "~/lib/api"
import { toast } from "sonner"
import { Mail, ArrowRight, Shield, CheckCircle2 } from "lucide-react"

export function ForgotPasswordForm({
  className,
  user,
  ...props
}: { user: UserType } & React.ComponentProps<"div">) {

  const userLabel = user === "seller" ? "Seller" : "Delivery Partner"

  async function sendResetLink(data: FormData) {
    const email = data.get("email")?.toString()

    if (!email) {
      toast.error("Please enter your email address")
      return
    }

    try {
      const userApi = user === "seller" ? api.seller : api.partner
      await userApi.forgotPassword({ email })
      toast.success("Reset link sent to your email!")
    } catch (error) {
      toast.error("Failed to send reset link. Please try again.")
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card className="overflow-hidden shadow-lg border-2">
        <CardContent className="grid p-0 md:grid-cols-2">
          {/* Reset Form */}
          <div className="p-8 md:p-10 flex flex-col justify-center">
            <CardHeader className="px-0 pb-6">
              <CardTitle className="text-2xl font-bold">Reset your password</CardTitle>
              <CardDescription className="text-base">
                We&apos;ll send you a link to reset your {userLabel} account password
              </CardDescription>
            </CardHeader>
            
            <form onSubmit={(e) => { e.preventDefault(); sendResetLink(new FormData(e.currentTarget)); }} className="space-y-6">
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
              
              <Button type="submit" className="w-full h-11 text-base font-semibold" size="lg">
                Send Reset Link
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
              
              <div className="text-center text-sm text-muted-foreground pt-2">
                Remember your password?{" "}
                <Link to={`/${user}/login`} className="text-primary font-medium hover:underline underline-offset-2">
                  Back to login
                </Link>
              </div>
            </form>
          </div>

          {/* Information Panel */}
          <div className="bg-gradient-to-br from-primary/10 via-primary/5 to-background border-l p-8 md:p-10 flex flex-col justify-center space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security & Privacy
              </h3>
              <ul className="space-y-4">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Secure process</p>
                    <p className="text-xs text-muted-foreground">Your email is verified before sending the reset link</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Time-limited link</p>
                    <p className="text-xs text-muted-foreground">The reset link expires after 24 hours for your security</p>
                  </div>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Check spam folder</p>
                    <p className="text-xs text-muted-foreground">If you don&apos;t see the email, check your spam or junk folder</p>
                  </div>
                </li>
              </ul>
            </div>
            
            <div className="pt-4 border-t">
              <p className="text-xs text-muted-foreground leading-relaxed">
                Need help? Contact our{" "}
                <Link to="#" className="text-primary hover:underline underline-offset-2">support team</Link>
                {" "}for assistance.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
