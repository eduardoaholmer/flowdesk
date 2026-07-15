# Multi-stage: `development` (hot reload via volume montado pelo docker-compose, usada
# por padrão em docker-compose.yml) e `production` (build estático servido por Nginx,
# sem Node.js em runtime) — ver docker-compose.prod.yml.
FROM node:22-alpine AS development

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci && chown -R node:node /app/node_modules

COPY . .

RUN chown -R node:node /app
USER node

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]

FROM node:22-alpine AS build

WORKDIR /app

# Vite embute variáveis `VITE_*` no bundle em build-time (não em runtime) — por isso
# precisa entrar como build-arg, diferente do backend (que lê `.env` em runtime).
ARG VITE_API_URL=http://localhost:8000/api/v1
ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# A imagem oficial roda o master process como root por padrão (necessário só para
# bindar portas <1024, o que não é o caso aqui — ver `listen 8080` em nginx.conf) —
# rodar como não-root mantém o mesmo padrão do container do backend.
RUN chown -R nginx:nginx /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown nginx:nginx /var/run/nginx.pid
USER nginx

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
