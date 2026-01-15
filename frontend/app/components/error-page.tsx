import { useRouteError, isRouteErrorResponse, Link, useNavigate } from "react-router";
import { Button } from "~/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "~/components/ui/card";
import { AlertCircle, Home, ArrowLeft, RefreshCw, Package } from "lucide-react";

export function ErrorPage() {
  const error = useRouteError();
  const navigate = useNavigate();
  
  let statusCode = 500;
  let title = "Something went wrong";
  let message = "An unexpected error occurred. Please try again.";
  let is404 = false;
  let isNetworkError = false;
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    statusCode = error.status;
    is404 = error.status === 404;
    
    if (is404) {
      title = "Page Not Found";
      message = "The page you're looking for doesn't exist or has been moved.";
    } else if (error.status === 403) {
      title = "Access Forbidden";
      message = "You don't have permission to access this resource.";
    } else if (error.status === 401) {
      title = "Unauthorized";
      message = "Please log in to access this page.";
    } else if (error.status >= 500) {
      title = "Server Error";
      message = "Our servers encountered an error. Please try again later.";
    } else {
      title = `Error ${error.status}`;
      message = error.statusText || error.data?.message || message;
    }
  } else if (error instanceof Error) {
    // Check for network errors
    if (error.message.includes("fetch") || error.message.includes("network") || error.message.includes("Failed to fetch")) {
      isNetworkError = true;
      title = "Connection Error";
      message = "Unable to connect to the server. Please check your internet connection and try again.";
    } else {
      message = error.message;
      if (import.meta.env.DEV) {
        stack = error.stack;
      }
    }
  }

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-gradient-to-b from-background via-background to-muted/20 p-6">
      <div className="w-full max-w-md">
        <Card className="shadow-lg border-2">
          <CardHeader className="text-center space-y-4">
            <div className="flex justify-center">
              {is404 ? (
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
                  <Package className="h-10 w-10 text-muted-foreground" />
                </div>
              ) : (
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10">
                  <AlertCircle className="h-10 w-10 text-destructive" />
                </div>
              )}
            </div>
            <div className="space-y-2">
              <CardTitle className="text-3xl font-bold">
                {is404 ? "404" : statusCode}
              </CardTitle>
              <CardDescription className="text-lg">
                {title}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-center text-muted-foreground">
              {message}
            </p>
            
            {isNetworkError && (
              <div className="rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>Tip:</strong> Check your internet connection and ensure the API server is running.
                </p>
              </div>
            )}

            {stack && import.meta.env.DEV && (
              <details className="mt-4">
                <summary className="cursor-pointer text-sm font-medium text-muted-foreground mb-2">
                  Error Details (Development Only)
                </summary>
                <pre className="w-full p-4 overflow-x-auto text-xs bg-muted rounded-md border">
                  <code>{stack}</code>
                </pre>
              </details>
            )}
          </CardContent>
          <CardFooter className="flex flex-col gap-3">
            <div className="flex gap-3 w-full">
              <Button
                variant="outline"
                onClick={handleGoBack}
                className="flex-1"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Go Back
              </Button>
              <Button
                asChild
                className="flex-1"
              >
                <Link to="/">
                  <Home className="mr-2 h-4 w-4" />
                  Home
                </Link>
              </Button>
            </div>
            {!is404 && (
              <Button
                variant="ghost"
                onClick={handleRefresh}
                className="w-full"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Page
              </Button>
            )}
          </CardFooter>
        </Card>

        {/* Additional help for 404 */}
        {is404 && (
          <div className="mt-6 text-center">
            <p className="text-sm text-muted-foreground mb-4">
              Looking for something specific?
            </p>
            <div className="flex flex-col sm:flex-row gap-2 justify-center">
              <Button asChild variant="outline" size="sm">
                <Link to="/seller/login">Seller Login</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link to="/partner/login">Partner Login</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
