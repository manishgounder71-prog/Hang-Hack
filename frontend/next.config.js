/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    domains: ['localhost'],
  },
  // Automatically tree-shake unused named exports from large packages
  experimental: {
    optimizePackageImports: [
      'lucide-react',
      'framer-motion',
      'recharts',
      '@react-three/drei',
      '@react-three/fiber',
    ],
  },
}

module.exports = nextConfig
