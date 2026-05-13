FROM nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
COPY prompt.js /usr/share/nginx/html/prompt.js
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8080
RUN sed -i 's/listen\s*80;/listen 8080;/' /etc/nginx/conf.d/default.conf
ENTRYPOINT ["/entrypoint.sh"]
