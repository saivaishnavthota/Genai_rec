FROM node:18-alpine

# Set environment variables
ENV NODE_ENV=development \
    GENERATE_SOURCEMAP=false \
    WATCHPACK_POLLING=true

WORKDIR /app

# Install curl for health checks
RUN apk add --no-cache curl

# Create non-root user
RUN addgroup -g 1001 -S nodejs \
    && adduser -S nextjs -u 1001

# Copy package files
COPY package*.json ./

# Install dependencies (include dev dependencies for development)
# Force reinstall to ensure all packages are properly installed
RUN npm install --legacy-peer-deps && npm cache clean --force

# Verify face-api.js installation (as root before switching users)
RUN npm list @vladmandic/face-api || (npm install @vladmandic/face-api --save --legacy-peer-deps && npm cache clean --force)

# Copy source code
COPY . .

# Set ownership
RUN chown -R nextjs:nodejs /app

# Switch to non-root user
USER nextjs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
