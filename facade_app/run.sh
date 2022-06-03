#!/bin/bash
if [[ ( -z "$SSL_CERT"  ||  -z "$SSL_KEY" ) ]] 
then 
    echo "Key or Cert missing, defaulting to selfsigned cert" 
    cat /data/ssl/gen_foobar.crt > /data/ssl/foobar.crt 
    cat /data/ssl/gen_foobar.key > /data/ssl/foobar.key 
else 
    echo "Key and Cert successfully supplied" 
    echo "$SSL_CERT" > /data/ssl/foobar.crt 
    echo "$SSL_KEY" > /data/ssl/foobar.key 
fi 
uwsgi wsgi.ini