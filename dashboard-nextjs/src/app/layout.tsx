import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'CBI-V14 | Soybean Oil Intelligence Platform',
  description: 'Institutional-grade soybean oil futures forecasting with Vertex AI AutoML',
  keywords: 'soybean oil, futures, trading, forecasting, AutoML, vertex AI',
  authors: [{ name: 'U.S. Oil Solutions' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#0D1421',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-background-primary text-text-primary`}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
