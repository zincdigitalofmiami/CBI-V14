/** @type {import('next').NextConfig} */
const nextConfig = {
  outputFileTracingRoot: __dirname,

  // Enable compression
  compress: true,
  
  // Performance optimizations (swcMinify is now default in Next.js 15)
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8080'
  }
}

module.exports = nextConfig
