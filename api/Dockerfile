# Node.js API Dockerfile
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies for node-gyp (needed for some packages)
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start the application
CMD ["npm", "run", "dev"]