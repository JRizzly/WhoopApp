DROP DATABASE IF EXISTS application_test;
CREATE DATABASE application_test WITH ENCODING 'UTF-8' LC_CTYPE='en_US.UTF8' LC_COLLATE='en_US.UTF8' TEMPLATE=template0;
GRANT ALL PRIVILEGES ON DATABASE application_test to %(username)s;
