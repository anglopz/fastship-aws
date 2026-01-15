import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Package, Lock, ArrowLeft, CheckCircle2, AlertCircle } from "lucide-react";
import { Link } from "react-router";
import { ThemeToggle } from "~/components/theme-toggle";
import { toast } from "sonner";

export default function SellerResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!token) {
    return (
      <div className="flex min-h-svh flex-col bg-gradient-to-b from-background via-background to-muted/20">
        <div className="container flex h-16 items-center gap-4 border-b justify-between">
          <Link to="/seller/login" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Login</span>
          </Link>
          <ThemeToggle />
        </div>
        <div className="flex flex-1 flex-col items-center justify-center p-6 md:p-10">
          <Card className="w-full max-w-md">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center gap-4 text-center">
                <AlertCircle className="h-12 w-12 text-destructive" />
                <h2 className="text-2xl font-bold">Invalid Reset Link</h2>
                <p className="text-muted-foreground">
                  The password reset link is missing or invalid. Please request a new password reset link.
                </p>
                <Button asChild className="w-full">
                  <Link to="/seller/login">Back to Login</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!password || !confirmPassword) {
      setError("Please fill in all fields");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setIsLoading(true);

    try {
      // Call backend API
      const formData = new FormData();
      formData.append("password", password);

      const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/seller/reset_password?token=${token}`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        // Check if response is HTML (backend returns HTML template)
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("text/html")) {
          // Backend returned HTML template - check if it's success or failure
          const html = await response.text();
          // If HTML contains success indicators, treat as success
          if (html.includes("success") || html.includes("Success") || html.includes("successfully")) {
            setIsSuccess(true);
            toast.success("Password reset successfully!");
            
            // Redirect to login after 2 seconds
            setTimeout(() => {
              navigate("/seller/login");
            }, 2000);
          } else {
            setError("Failed to reset password. The link may have expired. Please request a new one.");
            toast.error("Password reset failed");
          }
        } else {
          // JSON response (if backend is updated)
          setIsSuccess(true);
          toast.success("Password reset successfully!");
          
          // Redirect to login after 2 seconds
          setTimeout(() => {
            navigate("/seller/login");
          }, 2000);
        }
      } else {
        setError("Failed to reset password. The link may have expired. Please request a new one.");
        toast.error("Password reset failed");
      }
    } catch (err) {
      console.error("Reset password error:", err);
      setError("An error occurred. Please try again.");
      toast.error("An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="flex min-h-svh flex-col bg-gradient-to-b from-background via-background to-muted/20">
        <div className="container flex h-16 items-center gap-4 border-b justify-between">
          <Link to="/seller/login" className="flex items-center gap-2 font-semibold hover:opacity-80 transition-opacity">
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Login</span>
          </Link>
          <ThemeToggle />
        </div>
        <div className="flex flex-1 flex-col items-center justify-center p-6 md:p-10">
          <Card className="w-full max-w-md">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center gap-4 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
                  <CheckCircle2 className="h-8 w-8 text-green-600 dark:text-green-400" />
                </div>
                <h2 className="text-2xl font-bold">Password Reset Successful!</h2>
                <p className="text-muted-foreground">
                  Your password has been reset successfully. You will be redirected to the login page shortly.
                </p>
                <Button asChild className="w-full">
                  <Link to="/seller/login">Go to Login</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

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
        <div className="w-full max-w-md">
          {/* Branding Section */}
          <div className="mb-8 text-center space-y-4">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <Package className="h-6 w-6" />
              </div>
              <h1 className="text-3xl font-bold">Reset Password</h1>
            </div>
            <p className="text-lg text-muted-foreground">
              Enter your new password below
            </p>
          </div>

          <Card className="shadow-lg border-2">
            <CardHeader>
              <CardTitle>Create New Password</CardTitle>
              <CardDescription>
                Please enter your new password. Make sure it's at least 8 characters long.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="password" className="flex items-center gap-2">
                    <Lock className="h-4 w-4" />
                    New Password
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your new password"
                    required
                    minLength={8}
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">
                    Must be at least 8 characters long
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="flex items-center gap-2">
                    <Lock className="h-4 w-4" />
                    Confirm Password
                  </Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your new password"
                    required
                    minLength={8}
                    className="h-11"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full h-11 text-base font-semibold"
                  size="lg"
                  disabled={isLoading}
                >
                  {isLoading ? "Resetting Password..." : "Reset Password"}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
