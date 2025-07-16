FROM node:22-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "start"]