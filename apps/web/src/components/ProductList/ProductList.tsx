import { ProductCard } from "@/components/ProductCard/ProductCard"
import type { Product } from "@/shared/types"

import "./ProductList.scss"

interface ProductListProps {
  products: Product[]
}

export function ProductList({ products }: ProductListProps) {
  return (
    <div className="product-list">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  )
}
