#!/bin/bash
#
# How to use:
#   chmod +x samba-access.sh
#   ./samba-access.sh PATH_TO_SHARED_DIRECTORY  PERMISSIONS
#
#
# $1 = path , e.g. /home/myuser/publicdir
# $2 = permissions  ,  e.g  755
#


#if [ -z "$1" ];then
#  echo "How to use this script?"
#  echo "./installsamba.sh  PATH_TO_SHARED_DIRECTORY  PERMISSIONS"
#  exit 0
#fi

#if [ -z "$2" ];then
#  echo "Pass the persmissions of the directory you want to share as the second parameter."
#  exit 0
#fi

read -p "Insert Samba Directory: " dir
read -p "Set Permission Samba Directory: " permiss


echo "Creating main directory"
sudo mkdir $dir

read -p 'IP Monitor Ceph: ' ipmonitor

echo "mounting CephFS to directory"
sudo ceph-fuse -m $ipmonitor:6789 $dir

# Mounting directory at booting

echo "

none    $dir  fuse.ceph       ceph.id=admin,ceph.conf=/etc/ceph/ceph.conf,_netdev,defaults 0 0
" | sudo tee -a /etc/fstab

# Install Samba

samba_not_installed=$(dpkg -s samba 2>&1 | grep "not installed")
if [ -n "$samba_not_installed" ];then
  echo "Installing Samba"
  sudo apt-get install -y samba samba-common-bin
fi

echo "Creating public directory"
sudo mkdir $dir/public


# Configure directory that will be accessed with Samba

echo "

[File Server]
comment = Main Directory
path = $dir/public
public = yes
writable = yes
create mask = 0$permiss
force user = nobody
force group = nogroup
guest ok = yes
security = user
" | sudo tee -a /etc/samba/smb.conf


# Restart Samba service

sudo /etc/init.d/smbd restart
# Give persmissions to shared directory

sudo chmod -R $permiss $dir

# Start Ceph-FUSE at startup
sed -i "\$i ceph-fuse -m $ipmonitor:6789 $dir" /etc/rc.local


# Message to the User
 echo "To access the shared machine from Windows :"
 echo "\\\\$(ifconfig eno1 | sed -n 's/.*dr:\(.*\)\s Bc.*/\1/p')"
