import { ArrowUp, ChevronRight, Package2, PackageCheck, PackageX, ArrowUpRight, Truck } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "~/components/ui/dialog";
import { Button } from "./ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "./ui/card";

import { type Shipment, type ShipmentEvent } from "~/lib/client";
import ShipmentView, { ShipmentViewActions } from "./shipment-view";

const statusColors = {
    placed: {
        bgColor: "bg-blue-500",
        outlineColor: "outline-blue-500",
    },
    in_transit: {
        bgColor: "bg-orange-500",
        outlineColor: "outline-orange-500",
    },
    out_for_delivery: {
        bgColor: "bg-lime-500",
        outlineColor: "outline-lime-500",
    },
    delivered: {
        bgColor: "bg-green-400",
        outlineColor: "outline-green-400",
    },
    cancelled: {
        bgColor: "bg-grey-600",
        outlineColor: "outline-grey-600",
    },
}
const statusIcons = {
    placed: <ArrowUp className="size-4 text-primary-foreground" />,
    in_transit: <Truck className="size-4 text-primary-foreground" />,
    out_for_delivery: <ArrowUpRight className="size-4 text-primary-foreground" />,
    delivered: <PackageCheck className="size-4 text-primary-foreground" />,
    cancelled: <PackageX className="size-4 text-primary-foreground" />,
}

export default function ShipmentCard({ shipment }: { shipment: Shipment }) {
    const latestEvent = shipment.timeline && shipment.timeline.length > 0
        ? shipment.timeline[shipment.timeline.length - 1]
        : null;
    const latestStatus = latestEvent?.status || "placed";
    const statusColor = statusColors[latestStatus as keyof typeof statusColors] || statusColors.placed;

    return (
        <Card className="shadow-none" >
            <CardHeader>
                <div className="flex items-center space-x-4">
                    <div className="bg-secondary text-foreground flex size-16 items-center justify-center rounded-xl">
                        <Package2 className="size-8" />
                    </div>
                    <div>
                        <p className="text-gray-500">Shipment Number</p>
                        <p className="font-l font-medium">{shipment.id.slice(-10)}</p>
                    </div>
                </div>
            </CardHeader>
            <CardContent className="grid gap-4">
                <div className="rounded-xl p-4 bg-gray-50/50 border border-gray-200/50 relative overflow-hidden">
                    {/* Timeline line */}
                    <div className="absolute left-[60px] top-0 bottom-0 w-0.5 bg-gray-200" />
                    <div data-line className={`absolute left-[60px] top-[18px] bottom-0 w-0.5 ${statusColor.bgColor}`} />

                    {/* Timeline events */}
                    <div className="flex flex-col space-y-4 relative">
                        {latestEvent && (
                            <TimelineEvent hasOutline={true} event={latestEvent} bgColor={statusColor.bgColor} outlineColor={statusColor.outlineColor} />
                        )}
                        {
                            shipment.timeline && shipment.timeline.length > 1 &&
                            <TimelineEvent
                                event={shipment.timeline[shipment.timeline.length - 2]}
                                bgColor={statusColor.bgColor}
                                outlineColor={statusColor.bgColor} />
                        }
                    </div>
                </div>
            </CardContent>
            <CardFooter>
                <Dialog>
                    <DialogTrigger className="w-full">
                        <Button className="w-full">
                            View Details <ChevronRight />
                        </Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[700px] max-h-[90vh] flex flex-col p-0 gap-0">
                        <DialogHeader className="shrink-0 px-6 pt-6 pb-4 border-b">
                            <DialogTitle>{`Shipment #${shipment.id.slice(-8)}`}</DialogTitle>
                        </DialogHeader>
                        <div className="flex-1 overflow-y-auto px-6 py-4 min-h-0">
                            <ShipmentView shipment={shipment} />
                        </div>
                        <DialogFooter className="shrink-0 px-6 py-4 border-t bg-background">
                            <ShipmentViewActions shipment={shipment} />
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </CardFooter>
        </Card>
    )
}

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

function TimelineEvent({ event, bgColor, outlineColor, hasOutline = false }: { event: ShipmentEvent, bgColor: string, outlineColor: string, hasOutline?: boolean }) {
    return (
        <div className="flex items-start gap-3">
            <p className="text-xs text-muted-foreground w-[50px] shrink-0 pt-1 font-mono tabular-nums">
                {formatLocalTime(event.created_at)}
            </p>
            <div className={`w-8 h-8 ${bgColor} text-white flex items-center justify-center rounded-full shrink-0 ${hasOutline ? `outline-2 outline ${outlineColor} outline-offset-2` : ''}`}>
                <div className="scale-75">
                    {statusIcons[event.status as keyof typeof statusIcons] || statusIcons.placed}
                </div>
            </div>
            <p className="text-sm text-gray-800 flex-1 leading-relaxed pt-0.5">{event.description || event.status}</p>
        </div>
    );
}