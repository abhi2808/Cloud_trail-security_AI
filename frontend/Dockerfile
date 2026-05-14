# ── Frontend Dockerfile (multi-stage) ────────────────────────────
# Stage 1: Build the Vite/React app
# Stage 2: Serve with nginx
# ─────────────────────────────────────────────────────────────────

# ── Stage 1: Build ───────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install deps (layer cache)
COPY package.json package-lock.json ./
RUN npm ci

# Copy source and build
# VITE_API_URL must point to the EC2 public IP / domain at build time
# Pass it via --build-arg in docker build / docker-compose build
ARG VITE_API_URL=http://localhost:8000
ARG VITE_APP_SECRET_KEY=changeme
ARG VITE_AWS_REGION=ap-south-1

ENV VITE_API_URL=$VITE_API_URL \
    VITE_APP_SECRET_KEY=$VITE_APP_SECRET_KEY \
    VITE_AWS_REGION=$VITE_AWS_REGION

COPY . .
RUN npm run build

# ── Stage 2: Serve ───────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom config
COPY nginx.conf /etc/nginx/conf.d/app.conf

# Copy built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
