FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /repo
RUN corepack enable
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY frontend/package.json frontend/package.json
RUN pnpm install --frozen-lockfile

FROM node:20-alpine AS builder
RUN apk add --no-cache libc6-compat
WORKDIR /repo
RUN corepack enable
COPY --from=deps /repo/node_modules /repo/node_modules
COPY --from=deps /repo/frontend/node_modules /repo/frontend/node_modules
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY frontend frontend
RUN pnpm --filter frontend build

FROM node:20-alpine AS runner
RUN apk add --no-cache libc6-compat
WORKDIR /app
ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
COPY --from=builder /repo/frontend/.next/standalone ./
COPY --from=builder /repo/frontend/.next/static ./frontend/.next/static
COPY --from=builder /repo/frontend/public ./frontend/public

EXPOSE 3000

CMD ["node", "frontend/server.js"]
