
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import { toast } from "sonner"

import { ScanLine } from "lucide-react"
import {
    Drawer,
    DrawerContent,
    DrawerHeader,
    DrawerTitle
} from "~/components/ui/drawer"
import { Input } from "~/components/ui/input"
import {
    InputOTP,
    InputOTPGroup,
    InputOTPSeparator,
    InputOTPSlot,
} from "~/components/ui/input-otp"
import { Label } from "~/components/ui/label"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "~/components/ui/select"
import api from "~/lib/api"
import { ShipmentStatus, type Shipment, type ShipmentUpdate } from "~/lib/client"
import { cn, getLatestStatus } from "~/lib/utils"
import { Button } from "./ui/button"
import { SubmitButton } from "./ui/submit-button"
import { QrReader } from 'react-qr-reader'


const statusValues = [
    ShipmentStatus.InTransit,
    ShipmentStatus.OutForDelivery,
    ShipmentStatus.Delivered,
]

export function UpdateShipmentForm({
    className,
    onScan,
    shipment,
    ...props
}: { shipment?: Shipment | null, onScan: (id: string) => void } & React.ComponentPropsWithoutRef<"div">) {

    const queryClient = useQueryClient()

    const [status, setStatus] = useState<ShipmentStatus>()

    const shipments = useMutation({
        mutationFn: async ({
            id, update
        }: {
            id: string, update: ShipmentUpdate
        }) => {
            try {
                const response = await api.shipment.updateShipment({ id }, update)
                return response
            } catch (error) {
                // Re-throw to trigger onError
                throw error
            }
        },
        onSuccess: () => {
            toast.success("Shipment updated successfully")
            // Refetch queries immediately to get fresh data with timeline
            if (shipment?.id) {
                queryClient.refetchQueries({ queryKey: [shipment.id] })
            }
            queryClient.invalidateQueries({ queryKey: ["shipments"] })
        },
        onError: (error: any) => {
            console.error("Update shipment error:", error)
            const errorMessage = error?.response?.data?.message || error?.message || "Failed to update shipment"
            
            // Handle specific validation errors
            if (errorMessage.includes("cancelled") || errorMessage.includes("delivered")) {
                toast.error(errorMessage)
            } else if (status === "delivered") {
                toast.error("Invalid verification code")
            } else {
                toast.error(errorMessage)
            }
        }
    })

    const updateShipment = async (shipment: FormData) => {
        const id = shipment.get("id")!.toString()
        const verificationCode = shipment.get("verification-code")?.toString()
        const location = shipment.get("location")?.toString()
        const description = shipment.get("description")?.toString()

        if (!status && !location && !description) {
            toast.warning("Please provide an update")
            return
        }

        if (status === "delivered" && !verificationCode) {
            toast.warning("Please enter the verification code")
            return
        }

        shipments.mutate({
            id: id,
            update: {
                status: status,
                location: location ? parseInt(location) : null,
                description,
                verification_code: verificationCode,
            },
        })
    }

    const latestEvent = shipment?.timeline && Array.isArray(shipment.timeline) && shipment.timeline.length > 0
        ? shipment.timeline[shipment.timeline.length - 1]
        : null

    // Check if shipment cannot be updated
    const currentStatus = shipment ? getLatestStatus(shipment) : null
    const isCancelled = currentStatus === ShipmentStatus.Cancelled
    const isDelivered = currentStatus === ShipmentStatus.Delivered
    const cannotUpdate = isCancelled || isDelivered

    // Early return if shipment cannot be updated
    if (shipment && cannotUpdate) {
        return (
            <div className={cn("flex flex-col gap-6 p-8 max-w-[640px]", className)} {...props}>
                <div className="flex flex-col gap-4 p-6 border rounded-lg bg-muted/50">
                    <h1 className="text-xl font-bold">Shipment Cannot Be Updated</h1>
                    <div className="space-y-2">
                        {isCancelled && (
                            <p className="text-muted-foreground">
                                This shipment has been cancelled and cannot be updated. Cancelled shipments are in a final state.
                            </p>
                        )}
                        {isDelivered && (
                            <p className="text-muted-foreground">
                                This shipment has been delivered and cannot be updated. Delivered shipments are in a final state.
                            </p>
                        )}
                        <p className="text-sm text-muted-foreground mt-4">
                            Shipment ID: <span className="font-mono">{shipment.id.slice(-8)}</span>
                        </p>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className={cn("flex flex-col gap-6 p-8 max-w-[640px]", className)} {...props}>
            <form onSubmit={(e) => { e.preventDefault(); updateShipment(new FormData(e.currentTarget)); }}>
                <div className="flex flex-col gap-6">
                    <div className="flex flex-col gap-2">
                        <h1 className="text-xl font-bold">Update shipment</h1>
                    </div>
                    <div className="flex flex-col gap-6">
                        <div className="flex w-full items-center space-x-2">
                            <Input
                                value={shipment?.id ?? undefined}
                                type="text"
                                name="id"
                                required
                                placeholder="Shipment Id"
                            />
                            <QRScanner onScan={onScan}/>
                        </div>
                        <div className="grid gap-2">
                            <Label>Status</Label>
                            <Select name="status" value={status} onValueChange={(value) => {
                                setStatus(value as ShipmentStatus)
                            }}>
                                <SelectTrigger className="w-full">
                                    <SelectValue
                                        placeholder={shipment ? getLatestStatus(shipment) : "Shipment Status"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {statusValues.map((status) => (
                                        <SelectItem key={status} value={status}>
                                            {status}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        {
                            status === "delivered" && <div className="grid gap-2">
                                <Label htmlFor="verification-code">Verification Code</Label>
                                <InputOTP maxLength={6} name="verification-code">
                                    <InputOTPGroup>
                                        <InputOTPSlot index={0} />
                                        <InputOTPSlot index={1} />
                                        <InputOTPSlot index={2} />
                                    </InputOTPGroup>
                                    <InputOTPSeparator />
                                    <InputOTPGroup>
                                        <InputOTPSlot index={3} />
                                        <InputOTPSlot index={4} />
                                        <InputOTPSlot index={5} />
                                    </InputOTPGroup>
                                </InputOTP>
                            </div>
                        }
                        <div className="grid gap-2">
                            <Label htmlFor="location">Location</Label>
                            <Input
                                id="location"
                                name="location"
                                type="number"
                                placeholder={
                                    latestEvent?.location
                                        ? latestEvent.location.toString()
                                        : "e.g., 28001"
                                }
                            />
                            <p className="text-xs text-muted-foreground">
                                Enter the zip code where the shipment is currently located
                            </p>
                        </div>
                        <div className="grid gap-2">
                            <Label htmlFor="description">Description</Label>
                            <Input
                                id="description"
                                name="description"
                                type="text"
                                placeholder={
                                    latestEvent?.description
                                        ? latestEvent.description
                                        : "scanned at ..."
                                }
                            />
                            <p className="text-xs text-muted-foreground">
                                Add a description or notes about this update
                            </p>
                        </div>
                        <SubmitButton text="Update" pending={shipments.isPending} />
                    </div>
                </div>
            </form>
        </div>
    )
}
function QRScanner({ onScan }: { onScan: (id: string) => void }) {
    const [open, setOpen] = useState(false)

    return <Drawer open={open} onDrag={() => setOpen(false)}>
    
    <Button variant="outline" onClick={() => setOpen(true)}>
        <ScanLine />
    </Button>

    <DrawerContent>
      <DrawerHeader>
        <DrawerTitle>Scan Shipment Label</DrawerTitle>
      </DrawerHeader>
      {
        open && <>
            <video id="qr-scan-video"></video>
            <QrReader
                videoId="qr-scan-video"
                onResult={(result) => {
                    if (result) {
                        onScan(result.getText())
                        setOpen(false)
                    }
                }}
                constraints={{ facingMode: "environment" }}
            />
        </>
      }
    </DrawerContent>
  </Drawer>
  
}

