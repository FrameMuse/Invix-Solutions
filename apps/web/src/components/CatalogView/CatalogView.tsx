import { ProductList } from "@/components/ProductList/ProductList"
import type { Product } from "@/shared/types"

interface CatalogViewProps {
  products: Product[] | null
  loading?: boolean
}

export function CatalogView({ products, loading = false }: CatalogViewProps) {
  return (
    <main className="page">
      <h1 className="page__title">Каталог</h1>
      {loading ? (
        <p className="page__message">Загрузка...</p>
      ) : products === null ? (
        <p className="page__message">Каталог временно недоступен</p>
      ) : products.length === 0 ? (
        <p className="page__message">Пока нет товаров</p>
      ) : (
        <ProductList products={products} />
      )}
    </main>
  )
}
