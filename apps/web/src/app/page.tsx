import { CatalogClient } from "@/components/CatalogClient/CatalogClient"
import { CatalogLive } from "@/components/CatalogLive/CatalogLive"
import { CatalogView } from "@/components/CatalogView/CatalogView"
import { getProducts } from "@/shared/api"

const isStatic = process.env.NEXT_PUBLIC_STATIC === "true"

export default async function HomePage() {
  if (isStatic) {
    return <CatalogClient />
  }

  const products = await getProducts()

  return (
    <>
      <CatalogView products={products} />
      <CatalogLive />
    </>
  )
}
