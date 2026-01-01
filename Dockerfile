FROM nginx:alpine
COPY html/index.html /usr/share/nginx/html/index.html
EXPOSE 80
