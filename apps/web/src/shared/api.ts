import type { Product } from "@/shared/types"

const API_URL = (process.env.API_URL ?? "http://localhost:18000").replace(/\/$/, "")

export function isProduct(value: unknown): value is Product {
  if (typeof value !== "object" || value === null) {
    return false
  }

  const record = value as Record<string, unknown>

  return (
    typeof record.id === "string" &&
    typeof record.title === "string" &&
    typeof record.image_url === "string" &&
    typeof record.created_at === "string"
  )
}

export async function getProducts(): Promise<Product[] | null> {
  try {
    const response = await fetch(`${API_URL}/api/products`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000)
    })

    if (!response.ok) {
      return null
    }

    const data: unknown = await response.json()

    if (!Array.isArray(data) || !data.every(isProduct)) {
      return null
    }

    return data
  } catch {
    return null
  }
}
