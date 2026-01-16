import { Outlet } from "react-router";
import { Toaster } from "./components/ui/sonner";
import { ThemeProvider } from "next-themes";
import "./app.css";
import { AuthProvider } from "./contexts/AuthContext";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { ErrorPage } from "./components/error-page";

export default function Root() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Outlet />
          <Toaster />
        </AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export function ErrorBoundary() {
  return <ErrorPage />;
}
