# frontend/Dockerfile
#
# Two-stage build:
#   Stage 1 — node: runs `npm run build`, produces /app/dist
#   Stage 2 — nginx: serves the static dist with SPA fallback
#
# The nginx config rewrites all 404s back to index.html so React Router works.

# ── Stage 1: build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install deps first (cached if package.json unchanged)
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build


# ── Stage 2: serve ────────────────────────────────────────────────────────────
FROM nginx:alpine AS runtime

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# SPA-friendly nginx config
RUN cat > /etc/nginx/conf.d/app.conf << 'EOF'
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Serve static files, fall back to index.html for SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache busting for hashed assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Don't cache index.html
    location = /index.html {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }
}
EOF

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
