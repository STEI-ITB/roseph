#!/bin/bash

read -p "Nama Pool: " pool
read -p "Nama Image: " image

#Map RBD Device
echo "Mapping RBD Devices From Ceph"
#yrbd feature disable $pool/$image object-map fast-diff deep-flatten
block_device=$(rbd map $pool/$image)

#Install ISCI Target
echo "Installing iSCSI Target"
apt-get install -y tgt

#Create iSCSI Target
echo "Creating iSCSI Target an LUN"
tgtadm --lld iscsi --op new --mode target --tid 1 -T iqn.2018.com.tasds.disks
tgtadm --lld iscsi --op new --mode logicalunit --tid 1 --lun 1 -b $block_device
tgtadm --lld iscsi --op bind --mode target --tid 1 -I ALL

echo "Access with iSCSI Initiator to "
echo "\\\\$(ifconfig eno1 | sed -n 's/.*dr:\(.*\)\s Bc.*/\1/p')"
