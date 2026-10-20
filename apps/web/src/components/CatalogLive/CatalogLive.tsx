"use client"

import { useRouter } from "next/navigation"
import { useEffect } from "react"

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:18000").replace(/\/$/, "")

export function CatalogLive() {
  const router = useRouter()

  useEffect(() => {
    const source = new EventSource(`${API_URL}/api/events`)
    let opened = false

    source.onopen = () => {
      if (opened) {
        router.refresh()
      }

      opened = true
    }

    source.onmessage = () => {
      router.refresh()
    }

    return () => source.close()
  }, [router])

  return null
}
