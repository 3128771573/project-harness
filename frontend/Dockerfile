# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
# 使用国内 npm 镜像加速
RUN npm install --registry=https://registry.npmmirror.com
COPY . .
RUN npm run build

# Serve stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
