# Stage 1 : build React
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent
COPY frontend/ .
ARG VITE_API_BASE=https://stac-wiw.kbaddour.fr
RUN VITE_API_BASE=$VITE_API_BASE npm run build

# Stage 2 : nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80 443
