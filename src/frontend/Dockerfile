# Frontend Dockerfile for AWS build (build-only, deployed to S3+CloudFront)
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies needed for build)
# Use --legacy-peer-deps to resolve react-qr-reader peer dependency conflict with React 18
RUN npm ci --legacy-peer-deps

# Copy application files
COPY . .

# Build-time arguments for API URL
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the application
RUN npm run build

# Note: This Dockerfile is for building only
# The frontend is deployed to S3+CloudFront, not run as a container
# The build output in /app/dist is copied out and deployed to S3
