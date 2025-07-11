# Step 1: Build the React app
FROM node:22 AS build

WORKDIR /app
COPY . .

# Install dependencies
RUN npm install

# Build the optimized production app
RUN npm run build

# Step 2: Serve the build with a minimal web server
FROM nginx:stable-alpine

# Copy build from previous stage
COPY --from=build /app/build /usr/share/nginx/html

# ❗ Change nginx to listen on 8080 (Cloud Run default)
RUN sed -i 's/80;/8080;/g' /etc/nginx/conf.d/default.conf

# Expose port and start server
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
