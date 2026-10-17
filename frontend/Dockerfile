FROM node:20-slim AS base
WORKDIR /app
COPY package.json ./
RUN npm install

FROM base AS build
COPY . .
RUN npm run build

FROM node:20-slim AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/next.config.js ./next.config.js

EXPOSE 3000
CMD ["npm", "start"]
