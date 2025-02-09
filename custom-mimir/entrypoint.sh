#!/bin/sh
ADVERTISE_ADDR_REPLACE=$(ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{print $1}')
echo "IP address of eth0: $ADVERTISE_ADDR_REPLACE"

cp /etc/mimir-template.yaml /etc/mimir.yaml
sed -i "s/ADVERTISE_ADDR_REPLACE/$ADVERTISE_ADDR_REPLACE/" "/etc/mimir.yaml"

echo "New mimir.yaml:"
cat /etc/mimir.yaml

/usr/local/bin/mimir -config.file=/etc/mimir.yaml