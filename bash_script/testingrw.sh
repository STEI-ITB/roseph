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

read -p "Masukkan pool yang ingin di test " pool
read -p "Masukkan berama lama waktu test satuan (satuan sekon)" waktu
read -p "Masukkan nama file hasil testing " filename
read -p "Masukkan direktori file hasil testing " dir
touch $dir/$filename 
hasil="$(sudo rados bench -p $pool $waktu write --no-cleanup)"
hasil2="$(sudo rados bench -p $pool $waktu seq)"
hasil3="$(sudo rados bench -p $pool $waktu rand)"
echo "$hasil" >> $dir/$filename
echo "$hasil2" >> $dir/$filename
echo "$hasil3" >> $dir/$filename
rados -p $pool cleanup
echo "tes selesai dilakukan silahkan cek file di $dir/$filename"  

