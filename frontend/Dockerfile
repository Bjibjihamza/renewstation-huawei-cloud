# =============================================================================
#  RenewStation Frontend – Production Dockerfile (Vite + React + Tailwind)
# =============================================================================

# -------------------------- BUILD STAGE --------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dumb-init (keeps nginx from zombie processes)
RUN apk add --no-cache dumb-init

# Copy only package files first → max layer caching
COPY package*.json ./

# Install ALL dependencies (dev needed for build)
RUN npm ci

# Copy source code
COPY . .

# Build the app (creates /dist)
RUN npm run build

# -------------------------- PRODUCTION STAGE --------------------------
FROM nginx:alpine AS production

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config (critical for React Router!)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy dumb-init (optional but recommended)
COPY --from=builder /usr/bin/dumb-init /usr/bin/dumb-init

# Expose port
EXPOSE 80

# Use dumb-init to properly handle signals
ENTRYPOINT ["dumb-init", "--"]
CMD ["nginx", "-g", "daemon off;"]

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost/health || exit 1