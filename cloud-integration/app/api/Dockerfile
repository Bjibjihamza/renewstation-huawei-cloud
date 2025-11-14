# ============================================================================
#  RenewStation API – Cloud/ECS Dockerfile (multi-stage)
# ============================================================================

# -------------------------- BUILD STAGE --------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files only (cache friendly)
COPY package*.json ./

# Install all dependencies for the build
RUN npm ci

# Copy the rest of the source code
COPY . .

# (Optionnel) tests unitaires
# RUN npm test

# -------------------------- RUNTIME STAGE --------------------------
FROM node:20-alpine

WORKDIR /app

# User non-root pour la sécu
RUN addgroup -g 1001 -S nodejs \
  && adduser -S app -u 1001

# Copier uniquement ce qui est nécessaire
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/src ./src

# IMPORTANT : pas de .env copié → tout vient des variables d'env ECS
# (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, PORT, etc.)

USER app

EXPOSE 8000

# Commande de prod (sans nodemon)
CMD ["npm", "run", "start"]
