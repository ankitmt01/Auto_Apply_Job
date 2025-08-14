
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/tsconfig.json frontend/vite.config.ts frontend/tailwind.config.js frontend/postcss.config.js /app/
COPY frontend/src /app/src
COPY frontend/index.html /app/index.html
RUN npm install && npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist /app/dist
EXPOSE 5173
CMD ["npx", "serve", "-s", "dist", "-l", "tcp://0.0.0.0:5173"]

