# Frontend Dockerfile for Aura AI
# Multi-stage build: Build with Node, Serve with Nginx

# Stage 1: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
# Copy the built files from Stage 1 to the Nginx public folder
COPY --from=build /app/dist /usr/share/nginx/html
# Custom Nginx config to handle SPA routing (optional but recommended)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
