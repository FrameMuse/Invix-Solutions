import type { Metadata } from "next"
import type { ReactNode } from "react"

import { TelegramBridge } from "@/components/TelegramBridge/TelegramBridge"

import "./globals.scss"

export const metadata: Metadata = {
  title: "Каталог",
  description: "Каталог товаров"
}

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="ru">
      <body>
        <TelegramBridge />
        {children}
      </body>
    </html>
  )
}
