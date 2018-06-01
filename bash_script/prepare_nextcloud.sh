#!/bin/bash

read -p "Nama Pool: " pool
read -p "Nama Image: " image

echo "Moving conf file to /etc/ceph/"
mv ceph.c* /etc/ceph/

"Map RBD Device for Nextcloud Data"
rbd feature disable $pool/$image object-map fast-diff deep-flatten
block_device=$(rbdmap $pool/$image)

echo "Formatting Block Device with xfs"
apt-get install -y parted 
parted -s $block_device mklabel gpt mkpart primary xfs 0% 100%
mkfs.xfs -f $block_device

echo "Mounting Block Device"
mkdir /mnt/nextcloud-data
mount $block_device /mnt/nextcloud-data

echo "Add to fstab"
echo "
$block_device       /mnt/nextcloud-data      xfs     rw,noauto        0 0
" | tee -a /etc/fstab

echo "Add to /etc/ceph/rbdmap"
echo "
$pool/$image   id=admin,keyring=/etc/ceph/ceph.client.admin.keyring
" | tee -a /etc/ceph/rbdmap
systemctl enable rbdmap.service

echo "modify rc.local"
echo "
/usr/bin/mount /mnt/nextcloud-data
" | tee -a /etc/rc.local

echo "Run the install_nextcloud.yml at roseph/playbook/"
