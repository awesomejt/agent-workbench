import express from 'express'
import { createProxyMiddleware } from 'http-proxy-middleware'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const PORT = parseInt(process.env.PORT || '3000', 10)
const API_URL = process.env.AWB_API_URL || 'http://localhost:8000'

const app = express()

// Proxy /api/* to the Agent Workbench API (pathFilter preserves the full path)
app.use(
  createProxyMiddleware({
    pathFilter: '/api',
    target: API_URL,
    changeOrigin: true,
  }),
)

// Serve the Vite production build
app.use(express.static(path.join(__dirname, 'dist')))

// SPA fallback: all other routes return index.html
app.use((_req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'))
})

app.listen(PORT, () => {
  console.log(`Agent Workbench web server listening on :${PORT}`)
  console.log(`Proxying /api/* → ${API_URL}`)
})
