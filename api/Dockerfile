# =============================================================================
#  RenewStation API – Production-Ready Dockerfile (multi-stage)
# =============================================================================

# -------------------------- BUILD STAGE --------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install only build essentials (no python3/make/g++ needed — your deps are pure JS)
RUN apk add --no-cache git

# Copy package files
COPY package*.json ./

# Install ALL dependencies (including dev for build if you ever add build step)
RUN npm ci --only=production && npm install

# Copy source code
COPY . .

# Optional: Run tests (uncomment when you have them)
# RUN npm run test

# -------------------------- PRODUCTION STAGE --------------------------
FROM node:20-alpine AS production

WORKDIR /app

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Copy only necessary files from builder (no dev deps, no node_modules bloat)
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/src ./src
COPY --from=builder /app/.env.example ./.env.example

# Optional: copy config if you have one
# COPY --from=builder /app/config ./config

# Change ownership to non-root user
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 8000

# Healthcheck (critical for docker-compose depends_on)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

# Production start command (NO nodemon!)
CMD ["npm", "run", "start"]