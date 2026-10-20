"use client"

import { useEffect } from "react"

interface TelegramThemeParams {
  bg_color?: string
  text_color?: string
  hint_color?: string
}

interface TelegramWebApp {
  ready: () => void
  expand: () => void
  themeParams?: TelegramThemeParams
}

interface TelegramNamespace {
  WebApp?: TelegramWebApp
}

declare global {
  interface Window {
    Telegram?: TelegramNamespace
  }
}

const SCRIPT_SRC = "https://telegram.org/js/telegram-web-app.js"

function isDarkColor(color: string): boolean {
  const match = /^#([0-9a-f]{6})(?:[0-9a-f]{2})?$/i.exec(color)

  if (!match) {
    return false
  }

  const value = Number.parseInt(match[1], 16)
  const red = (value >> 16) & 255
  const green = (value >> 8) & 255
  const blue = value & 255

  return (red * 299 + green * 587 + blue * 114) / 1000 < 128
}

function applyTheme(webApp: TelegramWebApp): void {
  const theme = webApp.themeParams
  const root = document.documentElement

  if (!theme) {
    return
  }

  if (theme.bg_color) {
    root.style.setProperty("--tg-bg", theme.bg_color)
    root.dataset.theme = isDarkColor(theme.bg_color) ? "dark" : "light"
  }

  if (theme.text_color) {
    root.style.setProperty("--tg-text", theme.text_color)
  }

  if (theme.hint_color) {
    root.style.setProperty("--tg-muted", theme.hint_color)
  }
}

function initialize(): void {
  const webApp = window.Telegram?.WebApp

  if (!webApp) {
    return
  }

  webApp.ready()
  webApp.expand()
  applyTheme(webApp)
}

export function TelegramBridge() {
  useEffect(() => {
    if (window.Telegram?.WebApp) {
      initialize()
      return
    }

    const existing = document.querySelector<HTMLScriptElement>(`script[src="${SCRIPT_SRC}"]`)

    if (existing) {
      existing.addEventListener("load", initialize)

      return () => {
        existing.removeEventListener("load", initialize)
      }
    }

    const script = document.createElement("script")
    script.src = SCRIPT_SRC
    script.async = true
    script.addEventListener("load", initialize)
    document.head.appendChild(script)

    return () => {
      script.removeEventListener("load", initialize)
    }
  }, [])

  return null
}
