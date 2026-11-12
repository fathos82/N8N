FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund

COPY --chown=node:node src ./src
COPY --chown=node:node fixtures ./fixtures

ENV NODE_ENV=production
ENV HOST=0.0.0.0
ENV PORT=3907

USER node
EXPOSE 3907

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:3907/healthz || exit 1

CMD ["node", "src/server.js"]
