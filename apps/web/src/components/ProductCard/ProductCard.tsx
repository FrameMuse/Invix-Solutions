import type { Product } from "@/shared/types"

import "./ProductCard.scss"

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return ""
  }

  const day = String(date.getUTCDate()).padStart(2, "0")
  const month = String(date.getUTCMonth() + 1).padStart(2, "0")

  return `${day}.${month}.${date.getUTCFullYear()}`
}

interface ProductCardProps {
  product: Product
}

export function ProductCard({ product }: ProductCardProps) {
  return (
    <article className="product-card">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="product-card__image"
        src={product.image_url}
        alt={product.title}
      />
      <div className="product-card__body">
        <h2 className="product-card__title">{product.title}</h2>
        <time className="product-card__date" dateTime={product.created_at}>
          {formatDate(product.created_at)}
        </time>
      </div>
    </article>
  )
}
