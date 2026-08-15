FROM node:22-alpine

WORKDIR /app

COPY packages/bot/package*.json ./
COPY packages/bot .

RUN npm ci

# TODO: decomment after fullfilling all tasks
# == PROD ==
# RUN npm run build
# CMD ["npm", "start"]

# == DEV ==
CMD ["npm", "run", "dev"]