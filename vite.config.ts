import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    // Listen so Opera's http://localhost:5188/ works (IPv4 + IPv6 localhost)
    host: true,
    port: 5188,
    strictPort: true,
  },
  build: {
    assetsInlineLimit: 0,
  },
})
