import Link from "next/link"

export default function NotFound() {
  return (
    <main className="page">
      <h1 className="page__title">Страница не найдена</h1>
      <p className="page__message">
        <Link className="page__link" href="/">
          Вернуться в каталог
        </Link>
      </p>
    </main>
  )
}
