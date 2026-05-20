# Stage 1: Build React/Vite app
FROM node:20-alpine AS build

# Set the working directory inside the container
WORKDIR /app

# Copy package config files
COPY package*.json ./

# Install npm packages
RUN npm install

# Copy the rest of the frontend code
COPY . .



# Build the production bundle
RUN npm run build

# Stage 2: Serve using Nginx
FROM nginx:stable-alpine

# Copy the custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static files from build stage to Nginx web root
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
