-- Run as superuser: psql -U postgres -f sql/init.sql
CREATE DATABASE northstar;
CREATE USER northstar WITH PASSWORD 'northstar';
GRANT ALL PRIVILEGES ON DATABASE northstar TO northstar;
\c northstar
GRANT ALL ON SCHEMA public TO northstar;
