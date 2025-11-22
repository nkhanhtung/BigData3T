# frontend/Dockerfile

FROM node:18-alpine

WORKDIR /app

# Copy package trước để tận dụng cache Docker
COPY package.json package-lock.json* ./
RUN npm install

# Copy toàn bộ code
COPY . .

EXPOSE 5173

# --host để Vite chấp nhận kết nối từ ngoài container
CMD ["npm", "run", "dev", "--", "--host"]