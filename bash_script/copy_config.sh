#!/bin/bash

read -p "IP Nextcloud Node: " node

echo "Copy Configuration File"
scp /etc/ceph/ceph.c* $node:/home/tasds/

echo "Run install_nextcloud.sh on nextcloud node"
