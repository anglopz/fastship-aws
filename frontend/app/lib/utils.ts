import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { Shipment } from "./client";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

function getLatestStatus(shipment: Shipment): string {
  // Check if timeline exists and has items
  if (shipment.timeline && Array.isArray(shipment.timeline) && shipment.timeline.length > 0) {
    return shipment.timeline[shipment.timeline.length - 1].status
  }
  // Fallback to "placed" if timeline is not available
  return "placed"
}

function getShipmentsCountWithStatus(
  shipments: Shipment[],
  status: string
) {
  if (!shipments || !Array.isArray(shipments)) {
    return 0
  }
  return shipments.filter((shipment) => getLatestStatus(shipment) === status).length;
}

export { cn, getLatestStatus, getShipmentsCountWithStatus as getShipmentsCountForStatus }