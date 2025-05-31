# Use Node.js image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application files
COPY . .

# Expose the server port (default Express port or from env)
EXPOSE 5173

# Command to run the server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]