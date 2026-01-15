import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { ArrowUp, ArrowUpRight, Edit3, Package, PackageCheck, PackageX, Truck } from "lucide-react";
import { useContext, useState } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";

// Helper function to format timestamp in user's local timezone
// Backend sends timestamps without timezone (e.g., "2026-01-13T11:07:18"), so we assume UTC
function formatLocalTime(timestamp: string): string {
    // Check if timestamp already has timezone info (ends with Z, +, or has timezone offset like +00:00)
    const hasTimezone = timestamp.endsWith('Z') || 
                        timestamp.includes('+') || 
                        timestamp.match(/[+-]\d{2}:\d{2}$/);
    
    // If no timezone info, append 'Z' to indicate UTC
    const utcTimestamp = hasTimezone ? timestamp : `${timestamp}Z`;
    const date = new Date(utcTimestamp);
    
    // Validate date is valid
    if (isNaN(date.getTime())) {
        console.warn('Invalid timestamp:', timestamp);
        return timestamp; // Return original if invalid
    }
    
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false,
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
}

function formatLocalDate(timestamp: string): string {
    // Check if timestamp already has timezone info
    const hasTimezone = timestamp.endsWith('Z') || 
                        timestamp.includes('+') || 
                        timestamp.match(/[+-]\d{2}:\d{2}$/);
    
    // If no timezone info, append 'Z' to indicate UTC
    const utcTimestamp = hasTimezone ? timestamp : `${timestamp}Z`;
    const date = new Date(utcTimestamp);
    
    // Validate date is valid
    if (isNaN(date.getTime())) {
        console.warn('Invalid timestamp:', timestamp);
        return timestamp; // Return original if invalid
    }
    
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    });
}

import { Badge } from "~/components/ui/badge";
import { Button } from "~/components/ui/button";
import { AuthContext } from "~/contexts/AuthContext";
import api from "~/lib/api";
import { type Shipment, ShipmentStatus } from "~/lib/client";
import { getLatestStatus } from "~/lib/utils";


export default function ShipmentView({ shipment: shipmentProp }: { shipment: Shipment }) {

    // Fetch fresh shipment data to ensure timeline is loaded
    const { data: freshShipment, isLoading: isLoadingShipment } = useQuery({
        queryKey: [shipmentProp.id],
        queryFn: async () => {
            const response = await api.shipment.getShipment({ id: shipmentProp.id })
            return response.data
        },
        enabled: !!shipmentProp.id,
        // Always refetch when component mounts (dialog opens)
        refetchOnMount: "always",
        // Always consider data stale to force refetch
        staleTime: 0,
        // Don't use cached data, always fetch fresh
        gcTime: 0,
    })

    // Use fresh shipment data if available, otherwise use prop
    const shipment = freshShipment || shipmentProp

    // Show loading state while fetching fresh data (only if we don't have any data yet)
    if (isLoadingShipment && !freshShipment && !shipmentProp.timeline) {
        return (
            <div className="flex items-center justify-center p-8">
                <p className="text-muted-foreground">Loading shipment details...</p>
            </div>
        )
    }

    const details = [
        {
            "title": "Content",
            "description": shipment.content,
        },
        {
            "title": "Weight",
            "description": `${shipment.weight} kg`,
        },
        {
            "title": "Destination",
            "description": shipment.destination,
        },
        {
            "title": "Estimated Delivery",
            "description": shipment.estimated_delivery ? shipment.estimated_delivery.split("T")[0] : "N/A",
        },
    ]

    const statusColors = {
        placed: "bg-blue-500",
        in_transit: "bg-orange-500",
        out_for_delivery: "bg-lime-500",
        delivered: "bg-green-500",
        cancelled: "bg-gray-500",
    }

    const statusIcons = {
        placed: <ArrowUp className="size-4 text-white" />,
        in_transit: <Truck className="size-4 text-white" />,
        out_for_delivery: <ArrowUpRight className="size-4 text-white" />,
        delivered: <PackageCheck className="size-4 text-white" />,
        cancelled: <PackageX className="size-4 text-white" />,
    }

    return (
        <div className="flex flex-col gap-6 w-full relative pb-4">
            {/* Shipment Header */}
            <div className="flex items-start gap-4 pb-4 border-b">
                <div className="w-16 h-16 bg-gradient-to-br from-primary/10 to-primary/5 rounded-xl flex items-center justify-center shrink-0">
                    <Package size={32} className="text-primary" />
                </div>
                <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-2">Shipment Details</h3>
                    {shipment.tags && shipment.tags.length > 0 && (
                        <div className="flex gap-2 flex-wrap">
                            {shipment.tags.map((tag, index) => (
                                <Badge variant="secondary" key={index} className="text-xs">{tag.name}</Badge>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Shipment Info Grid */}
            <div className="grid grid-cols-2 gap-4 mb-6 pb-4 border-b">
                {details.map((item, index) => (
                    <div key={index} className="flex flex-col gap-1 p-3 rounded-lg bg-muted/30">
                        <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{item.title}</h4>
                        <p className="text-base text-foreground font-semibold">{item.description}</p>
                    </div>
                ))}
            </div>

            {/* Timeline Section */}
            <div className="space-y-3 pt-2">
                <h4 className="text-sm font-semibold text-foreground">Timeline</h4>
                {shipment.timeline && shipment.timeline.length > 0 ? (
                    <div className="relative">
                        {/* Timeline events container */}
                        <div className="flex flex-col space-y-4 relative">
                            {shipment.timeline.map((item, index) => {
                                const isLatest = index === shipment.timeline.length - 1;
                                const bgColor = statusColors[item.status as keyof typeof statusColors] || statusColors.placed;
                                const icon = statusIcons[item.status as keyof typeof statusIcons] || statusIcons.placed;
                                
                                return (
                                    <div key={index} className="flex items-start gap-3 relative pb-2">
                                        {/* Timeline line - only between events, not extending beyond */}
                                        {!isLatest && (
                                            <div className="absolute left-[68px] top-[28px] h-[calc(100%+0.5rem)] w-0.5 bg-gray-200 z-0" />
                                        )}
                                        
                                        {/* Time - Always visible */}
                                        <div className="w-[60px] shrink-0 pt-1">
                                            <p className="text-xs font-medium text-muted-foreground font-mono tabular-nums">
                                                {formatLocalTime(item.created_at)}
                                            </p>
                                        </div>
                                        
                                        {/* Icon */}
                                        <div className={`w-7 h-7 ${bgColor} text-white flex items-center justify-center rounded-full shrink-0 relative z-20 ${isLatest ? 'outline-2 outline outline-offset-2 outline-primary' : ''}`}>
                                            {icon}
                                        </div>
                                        
                                        {/* Content */}
                                        <div className="flex-1 min-w-0 pt-0.5 relative z-10">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-sm font-medium text-foreground capitalize">
                                                    {item.status.replace('_', ' ')}
                                                </span>
                                                {item.location && (
                                                    <Badge variant="outline" className="text-xs">
                                                        {item.location}
                                                    </Badge>
                                                )}
                                                {/* Timestamp badge next to status */}
                                                <span className="text-xs text-muted-foreground font-mono tabular-nums">
                                                    {formatLocalTime(item.created_at)}
                                                </span>
                                            </div>
                                            {item.description && (
                                                <p className="text-sm text-muted-foreground leading-relaxed">
                                                    {item.description}
                                                </p>
                                            )}
                                            <p className="text-xs text-muted-foreground mt-1">
                                                {formatLocalDate(item.created_at)}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-8 text-muted-foreground">
                        <PackageX className="size-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">No timeline events available</p>
                    </div>
                )}
            </div>

        </div>
    );
}

// Action buttons component to be used in DialogFooter (outside scrollable area)
export function ShipmentViewActions({ shipment }: { shipment: Shipment }) {
    const { user } = useContext(AuthContext)
    const navigate = useNavigate()
    const [isCancelling, setIsCancelling] = useState(false)
    const queryClient = useQueryClient()

    // Cancel shipment mutation
    const cancelShipmentMutation = useMutation({
        mutationFn: async (id: string) => {
            const response = await api.shipment.cancelShipment({ id })
            return response.data
        },
        onSuccess: () => {
            toast.success("Shipment cancelled successfully")
            queryClient.invalidateQueries({ queryKey: ["shipments"] })
            queryClient.refetchQueries({ queryKey: [shipment.id] })
            setIsCancelling(false)
        },
        onError: (error: any) => {
            console.error("Cancel shipment error:", error)
            const errorMessage = error.response?.data?.message || "Failed to cancel shipment"
            toast.error(errorMessage)
            setIsCancelling(false)
        }
    })

    const handleCancelShipment = async () => {
        if (!shipment.id) return
        
        const currentStatus = getLatestStatus(shipment)
        if (currentStatus === ShipmentStatus.Cancelled) {
            toast.warning("Shipment is already cancelled")
            return
        }

        if (!confirm("Are you sure you want to cancel this shipment? This action cannot be undone.")) {
            return
        }

        setIsCancelling(true)
        cancelShipmentMutation.mutate(shipment.id)
    }

    const currentStatus = getLatestStatus(shipment)
    const isCancelled = currentStatus === ShipmentStatus.Cancelled
    const isDelivered = currentStatus === ShipmentStatus.Delivered

    return (
        <>
            {
                user === "seller" && !isCancelled && !isDelivered &&
                <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleCancelShipment}
                    disabled={isCancelling || cancelShipmentMutation.isPending}
                >
                    <PackageX className="size-4 mr-2" />
                    {isCancelling || cancelShipmentMutation.isPending ? "Cancelling..." : "Cancel Shipment"}
                </Button>
            }
            {
                user === "partner" && !isCancelled && !isDelivered &&
                <Button onClick={() => {
                    navigate({
                        pathname: "/update-shipment",
                        search: `?id=${shipment.id}`,
                    })
                }} size="sm">
                    <Edit3 className="size-4 mr-2" />
                    Update Status
                </Button>
            }
            {
                user === "partner" && (isCancelled || isDelivered) &&
                <Button disabled size="sm" variant="outline">
                    <Edit3 className="size-4 mr-2" />
                    {isCancelled ? "Shipment Cancelled" : "Shipment Delivered"}
                </Button>
            }
        </>
    )
}