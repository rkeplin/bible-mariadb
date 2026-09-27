FROM mariadb:10.11

COPY ./initdb.d/ /docker-entrypoint-initdb.d
