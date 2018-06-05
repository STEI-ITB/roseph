#!/bin/bash
#
# How to use:
#   chmod +x samba-access.sh
#   ./samba-S
#
#
#


#if [ -z "$1" ];then
#  echo "How to use this script?"
#  echo "bash the script"
#  exit 0
#fi

#read -p "Masukkan pool yang ingin di test: " pool
#read -p "Masukkan berama lama waktu test satuan (satuan sekon): " waktu
read -p "Masukkan nama file hasil testing: " filename
sudo chmod +r /etc/ceph/ceph.client.admin.keyring

counter=1
while [ $counter -le 3 ]; do
        touch $filename-iterasi$counter
        echo "$counter"
        hasil="$(sudo rados bench -p scbench 10 write --no-cleanup)"
        hasil2="$(sudo rados bench -p scbench 10 seq)"
        hasil3="$(sudo rados bench -p scbench 10 rand)"
	echo "WRITE" >> $filename-iterasi$counter
        echo "$hasil" >> $filename-iterasi$counter
	echo " " >> $filename-iterasi$counter
        echo "Seq READ" >> $filename-iterasi$counter
        echo "$hasil2" >> $filename-iterasi$counter
        echo " " >> $filename-iterasi$counter
	echo "Rand READ" >> $filename-iterasi$counter
        echo "$hasil3" >> $filename-iterasi$counter
        rados -p scbench cleanup
        counter=$(( $counter + 1 ))
done

echo "tes selesai dilakukan silahkan cek file di $filename"


