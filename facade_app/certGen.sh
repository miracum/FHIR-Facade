
if [ -e $KEY_LOCATION ]
then
    if [ -e $CERT_LOCATION ]
    then
        echo "Key and Certificate found."
    else
        echo "Key was found, but cert is missing. Generating new Key/Cert pair. Set KEY_LOCATION & CERT_LOCATION to the respective Paths."
        openssl genrsa -out foobar.key 2048
        openssl req -new -key foobar.key -out foobar.csr -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com"
        openssl x509 -req -days 365 -in foobar.csr -signkey foobar.key -out foobar.crt
    fi
else
    echo "Key and cert are missing. Generating new Key/Cert pair. Set KEY_LOCATION & CERT_LOCATION to the respective Paths."
    openssl genrsa -out foobar.key 2048
    openssl req -new -key foobar.key -out foobar.csr -subj "/C=GB/ST=London/L=London/O=Global Security/OU=IT Department/CN=example.com"
    openssl x509 -req -days 365 -in foobar.csr -signkey foobar.key -out foobar.crt
fi
