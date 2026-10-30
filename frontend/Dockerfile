FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY src/ /usr/share/nginx/html/

EXPOSE 80

HEALTHCHECK --interval=5s --timeout=5s --retries=5 --start-period=5s \
  CMD wget -q -O - http://127.0.0.1:80/ || exit 1
