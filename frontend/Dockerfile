# ---------- Build stage ----------
FROM node:20-alpine AS builder

WORKDIR /app

# Backend URL is baked into the bundle at build time
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Copy package manifests (yarn.lock is optional — pattern uses wildcard so
# the build works whether or not it was committed to the repo)
COPY package.json ./
COPY yarn.lock* ./
RUN yarn install --network-timeout 600000

COPY . .
RUN yarn build

# ---------- Runtime stage ----------
FROM nginx:1.27-alpine

# Custom nginx config that serves SPA + proxies /api
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
