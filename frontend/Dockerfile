# Build Angular production, serve static + reverse proxy /api → backend (docker-compose service "api")
FROM node:20-alpine AS build
WORKDIR /src
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration=production

FROM nginx:1.27-alpine
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist/health-bot-frontend/browser /usr/share/nginx/html
EXPOSE 80
