FROM mariadb:10.4.2-bionic

COPY ./initdb.d/ /docker-entrypoint-initdb.d
