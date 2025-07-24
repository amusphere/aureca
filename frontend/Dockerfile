FROM node:22-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source code
COPY . .

# Set variables
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "start", "--", "--port", "8080"]