/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['lightweight-charts']
  },
  
  // Optimize for TradingView and charting libraries
  webpack: (config, { isServer }) => {
    // Handle TradingView library
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    }

    // Optimize for charting libraries
    if (!isServer) {
      config.resolve.alias = {
        ...config.resolve.alias,
      }
    }

    return config
  },

  // Images for charts and graphics
  images: {
    domains: ['s3.tradingview.com', 'tradingview.com'],
    unoptimized: false,
  },

  // API routes for backend integration
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NEXT_PUBLIC_API_BASE_URL 
          ? `${process.env.NEXT_PUBLIC_API_BASE_URL}/:path*`
          : 'http://localhost:8080/:path*'
      }
    ]
  },

  // Enable compression
  compress: true,
  
  // Performance optimizations
  swcMinify: true,
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
  }
}

module.exports = nextConfig
