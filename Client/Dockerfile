# Step 1: Build the React app
FROM node:22 AS build

WORKDIR /app
COPY . .
RUN npm install
RUN npm run build

# Step 2: Serve the build with nginx
FROM nginx:stable-alpine

# Copy production build
COPY --from=build /app/build /usr/share/nginx/html

# ✅ Custom NGINX config that handles React routing + port 8080
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
