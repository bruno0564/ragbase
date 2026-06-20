# Imagen del frontend: compila con Vite y sirve los estáticos con nginx.
# El contexto de build es la raíz del repo.

FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
# La URL del backend se hornea en el bundle en tiempo de build. Por defecto el
# navegador (fuera de la red de Docker) habla con el backend publicado en el host.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
