# =============================================================================
# Genesis AI — Frontend Dockerfile
# Multi-stage: deps → build → standalone runner
# =============================================================================

# ── Dependencies stage ────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app

# Copy only package files to leverage Docker cache
COPY package.json package-lock.json* ./
# Use npm ci for deterministic, faster builds (respects lockfile exactly)
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

# ── Builder stage ─────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the Next.js app (generates .next/standalone)
RUN npm run build

# ── Runner stage ──────────────────────────────────────────────────────────
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy standalone build output (includes server.js + necessary chunks)
COPY --from=builder /app/.next/standalone ./
# Copy static assets (these are served directly, not bundled in standalone)
COPY --from=builder /app/.next/static ./.next/static
# Copy public assets
COPY --from=builder /app/public ./public

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run the standalone server
CMD ["node", "server.js"]
