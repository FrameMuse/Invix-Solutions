"use client"

import { useEffect, useState } from "react"

import { CatalogView } from "@/components/CatalogView/CatalogView"
import { isProduct } from "@/shared/api"
import type { Product } from "@/shared/types"

const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:18000").replace(/\/$/, "")

async function fetchProducts(): Promise<Product[] | null> {
  try {
    const response = await fetch(`${API_URL}/api/products`)

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

function mergeProducts(current: Product[] | null, incoming: Product[]): Product[] {
  if (current === null) {
    return incoming
  }

  const ids = new Set(incoming.map((product) => product.id))
  const fresh = current.filter((product) => !ids.has(product.id))

  return [...fresh, ...incoming]
}

function addProduct(current: Product[] | null, product: Product): Product[] {
  if (current === null) {
    return [product]
  }

  if (current.some((item) => item.id === product.id)) {
    return current
  }

  return [product, ...current]
}

export function CatalogClient() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function load() {
      const data = await fetchProducts()

      if (!active) {
        return
      }

      if (data) {
        setProducts((current) => mergeProducts(current, data))
      }

      setLoading(false)
    }

    load()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    const source = new EventSource(`${API_URL}/api/events`)
    let opened = false

    source.onopen = () => {
      if (opened) {
        void fetchProducts().then((data) => {
          if (data) {
            setProducts((current) => mergeProducts(current, data))
          }
        })
      }

      opened = true
    }

    source.onmessage = (event) => {
      try {
        const data: unknown = JSON.parse(event.data)

        if (!isProduct(data)) {
          return
        }

        setProducts((current) => addProduct(current, data))
        setLoading(false)
      } catch {
        return
      }
    }

    return () => source.close()
  }, [])

  return <CatalogView products={products} loading={loading} />
}
