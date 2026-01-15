FROM node:20-alpine

WORKDIR /app

# Install dependencies first (for better caching)
COPY package*.json .npmrc* ./
RUN npm install --legacy-peer-deps && \
    npm cache clean --force

# Copy app files
COPY . .

# Expose port
EXPOSE 5173

# Use npm run dev which now uses npx vite (bypasses permission issues)
CMD ["sh", "-c", "npm run dev -- --host 0.0.0.0 --port 5173"]
