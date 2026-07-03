import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Genesis AI - The Self-Evolving AI Operating System',
  description: 'The AI That Evolves Because It Remembers. Powered by Cognee.',
  keywords: ['AI', 'memory', 'knowledge graph', 'self-evolving', 'cognee'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen antialiased">
        {children}
      </body>
    </html>
  )
}
