# Use the official Node.js image.
FROM node:14

# Set the working directory.
WORKDIR /usr/src/app

# Copy package.json and package-lock.json.
COPY package*.json ./

# Install app dependencies.
RUN npm install

# Copy the app source code to the container.
COPY . .

# Expose the port your app runs on (change if your app uses a different port).
EXPOSE 3000

# Command to run your app.
CMD ["npm", "start"]
