# Build stage
FROM node:22 AS build

WORKDIR /app

# Step 1: Install dependencies using ONLY the package.json
# We ignore the local lockfile and force a fresh resolution
COPY package.json ./
RUN npm install && npm install @tailwindcss/oxide

# Step 2: Granularly copy only the source and config files
# This guarantees no local node_modules or locks are leaked into the container
COPY src ./src
COPY public ./public
COPY components.json index.html tsconfig.json vite.config.ts ./

# Step 3: Build the project
RUN npm run build

# Use a lightweight Nginx server to serve the build
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Copy the custom API Gateway configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
