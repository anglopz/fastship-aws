import { Link } from "react-router";
import { ForgotPasswordForm } from "~/components/forgot-password-form";
import { ArrowLeft, Package } from "lucide-react";
import { ThemeToggle } from "~/components/theme-toggle";

export default function SellerForgotPasswordPage() {
  return (
    <div className="flex min-h-svh flex-col bg-gradient-to-b from-background via-background to-muted/20">
      {/* Header */}
      <div className="container flex h-16 items-center gap-4 border-b justify-between">
        <Link to="/seller/login" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
          <ArrowLeft className="h-4 w-4" />
          <span>Back to Login</span>
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
                <Package className="h-6 w-6" />
              </div>
              <h1 className="text-3xl font-bold">Reset Password</h1>
            </div>
            <p className="text-lg text-muted-foreground">
              Enter your email to receive password reset instructions
            </p>
          </div>

          <ForgotPasswordForm user="seller" />
        </div>
      </div>
    </div>
  )
}
