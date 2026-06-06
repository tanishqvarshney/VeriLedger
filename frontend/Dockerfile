FROM node:20-slim

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

# Expose Vite dev server port
EXPOSE 3000

# Start Vite dev server on 0.0.0.0:3000
CMD ["npm", "run", "dev"]
