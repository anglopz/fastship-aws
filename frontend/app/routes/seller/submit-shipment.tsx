import { useContext } from "react"
import { Navigate } from "react-router"
import { AppSidebar } from "~/components/app-sidebar"
import { SubmitShipmentForm } from "~/components/submit-shipment-form"
import { Separator } from "~/components/ui/separator"
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "~/components/ui/sidebar"
import { AuthContext } from "~/contexts/AuthContext"

export default function SubmitShipmentPage() {

  const { token, user } = useContext(AuthContext)
  if (!token) {
    return <Navigate to="/" />
  }
  if (user !== "seller") {
    return <Navigate to="/dashboard" />
  }

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "19rem",
        } as React.CSSProperties
      }
    >
      <AppSidebar currentRoute="Submit Shipment" />
      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator
            orientation="vertical"
            className="mr-2 data-[orientation=vertical]:h-4"
          />
          <h2>Submit Shipment</h2>
        </header>
        <div className="flex flex-1 flex-col gap-4 p-4 pt-0 max-w-[600px]">
          <SubmitShipmentForm />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
