#!/bin/sh

echo "GENERATING RABBITMQ CONF TEMPLATE..."

apt-get update && apt-get install -y gettext

# NOTE: We set dollar here to escape $var's in nginxconf, instead we write
# ${DOLLAR}var to escape it.
export DOLLAR='$'

# Swap configs based on SSL
if [[ $SSL_CERTIFICATE ]]
then
    echo "Using SSL certificate '${SSL_CERTIFICATE}'"
    envsubst < app/docker/rabbitmq/rabbitmq.config > /etc/rabbitmq/rabbitmq.config
else
    echo "No SSL certificate env var (SSL_CERTIFICATE) found"
fi

echo "/etc/rabbitmq/rabbitmq.config:"
echo | cat /etc/rabbitmq/rabbitmq.config

#rabbitmq-server
