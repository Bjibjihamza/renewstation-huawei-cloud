# ============================================================================
#  RenewStation Frontend – Cloud/ECS Dockerfile (Vite + React)
# ============================================================================

# -------------------------- BUILD STAGE --------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Installer les deps
COPY package*.json ./
RUN npm ci

# Copier le code
COPY . .

# Build Vite → dist/
RUN npm run build

# -------------------------- RUNTIME STAGE --------------------------
FROM nginx:alpine

# Nettoyer le site par défaut
RUN rm -rf /usr/share/nginx/html/*

# Copier les fichiers buildés
COPY --from=builder /app/dist /usr/share/nginx/html

# Copier ta config Nginx custom (gère React Router, /health, etc.)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Nginx en mode "foreground"
CMD ["nginx", "-g", "daemon off;"]
