#MyCephApp merupakan aplikasi untuk memudahkan deployment dan operasional bagi sistem penyimpanan Ceph
#Kontributor: Ghazy Mahendra, Alfian Azizi, Andrew Filbert D
#Versi 0.95 (1 Juni 2018)

#Mengimpor fungsi-fungsi dari library lain
from flask import Flask, request, render_template, flash, redirect, send_file
import requests
import json
import math
from flask_wtf import Form
from wtforms import validators,StringField, IntegerField,SubmitField, BooleanField, SelectField
from flask_cors import CORS
from blockdevice import PilihCapsMon, PilihCapsOsd, PilihCapsMds
from blockdevice import newImage, newPool, list_image, image_info, editImage, deleteImage
import subprocess
import yaml
import optparse
import ipcalc

#persiapan program
app = Flask(__name__)
cors = CORS(app, resources={r"10.10.6.1:5000/api/v0.1/*": {"Access-Control-Allow-Origin": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'development key'
headers = {'Access-Control-Max-Age' : '3600',
           'Content-Type' : 'text/plain',
           'Content-Length' : '0',
           'Access-Control-Allow-Origin': '*',
           "Access-Control-Allow-Credentials": "True",
           'Access-Control-Allow-Methods': 'GET, POST, OPTIONS,PUT',
           'Access-Control-Allow-Headers': 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range',
           'Access-Control-Expose-Headers': 'Content-Length'}

#Definisi kelas untuk form, dibuat mengunakan flask-wtf
class BuatUser(Form):
    userID = StringField('userID')
    OSDr   = BooleanField('read')
    OSDw   = BooleanField('write')
    OSDx   = BooleanField('execute')
    MONr   = BooleanField('read')
    MONw   = BooleanField('write')
    MONx   = BooleanField('execute')
    MDSr   = BooleanField('read')
    MDSw   = BooleanField('write')
    MDSx   = BooleanField('execute')
    pool   = SelectField('Pool')
    submit = SubmitField()

class BuatPool(Form):
    namaPool = StringField('Nama Pool')
    PGnum = IntegerField('PG Number')
    PGPnum = IntegerField('PGP Number')
    submit = SubmitField()

class BuatImage(Form):
    namaPool = SelectField('Nama Pool')
    namaImage = StringField('Nama Image')
    kapasitas = IntegerField('Kapasitas dalam GB')
    submit = SubmitField()

class TambahOSD(Form):
    ip_addr = StringField('Alamat IP')
    device  = StringField('Device untuk OSD Baru')
    isjournal = BooleanField('Menggunakan Journal')
    journal = StringField('Device untuk Journal - Opsional')
    submit = SubmitField()

class deployform(Form):
    release = SelectField('Versi Ceph yang digunakan', choices=[('jewel','jewel'),('luminous','luminous')])
    ipmon   = StringField('IP komputer monitor')
    iposd   = StringField('IP komputer OSD')
    pubnet  = StringField('Alamat IP jaringan publik')
    clnet   = StringField('Alamat IP jaringan cluster')
    osdtype = SelectField('Jenis OSD', choices=[('FileStore','FileStore'),('BlueStore','BlueStore')])
    rgw_addr= StringField('Alamat Rados Gateway')
    device  = StringField('Device untuk OSD Baru')
    isjournal = BooleanField('Menggunakan Journal')
    journal = StringField('Device untuk Journal - Opsional')
    submit = SubmitField()

class addnode(Form):
    ip_addr = StringField('Alamat IP')
    hostname= StringField('Nama Host')
    ismon   = BooleanField('Digunakan sebagai MON?')
    isosd   = BooleanField('Digunakan sebagai OSD?')
    isrgw   = BooleanField('Digunakan sebagai RGW?')
    submit = SubmitField()

class purgeform(Form):
   yakin1 = BooleanField('Apakah Anda yakin menghapus cluster ini?')
   yakin2 = BooleanField('Apakah Anda sudah mengamankan data penting pada cluster ini?')
   ireallymeanit = StringField('Tulis yes untuk konfirmasi')
   submit = SubmitField('Hapus')

#Modul Started
#Tujuan: Menerima pengguna sistem sebelum sistem berjalan, memberikan opsi untuk deployment sistem baru dan purging sistem lama
#	 juga memberi keterangan tentang modul-modul lain
#Masukan: None
#Luaran : Laman
@app.route('/')
def started():
	return render_template('starting.html')

#Modul Deployment
#Tujuan: Melakukan instalasi awal untuk komputer baremetal hingga sistem dapat dijalankan dan dipantau
#Masukan: Release ver, IP monitor, IP osd, public network, cluster network, jenis osd, IP RGW, alamat device, penggunaan jurnal
#	 alamat jurnal
#Luaran : Laman dan deployment
#Keterangan : Deployment memakan waktu lama
@app.route('/Deploy', methods = ['GET', 'POST'])
def deploy():
    stream = open('deploy.yml','r+')
    hosts = []
    if stream !='':
        hosts = yaml.load(stream)
    form = deployform(request.form)
    if request.method == 'POST':
	if form.validate() == False:
           return render_template('deploy.html', form=form, hosts=hosts)
        else:
	   #Persiapkan data yang akan dimasukkan ke all.yml
	   c = 0
	   monip = ''
	   osdip = ''
	   rgwip = ''
	   while c != len(hosts):
		if hosts[c]['ismon']:
			if monip == '':
				monip = hosts['ip_addr']
			else:
				monip = monip+','+hosts['ip_addr']
                if hosts[c]['isosd']:
                        if osdip == '':
                                osdip = hosts['ip_addr']
                        else:
                                osdip = osdip+','+hosts['ip_addr']
                if hosts[c]['isrgw']:
                        if rgwip == '':
                                rgwip = hosts['ip_addr']
                        else:
                                rgwip = rgwip+','+hosts['ip_addr']
		c = c +1
	   #edit all.yml menggunakan pyyaml	
	   stream = open('../ceph-ansible/group_vars/all.yml','r')
	   allyml = yaml.load(stream)
	   allyml['ceph_stable_release'] = form.release.data
	   allyml['monitor_address'] = monip
           allyml['public_network'] =  hosts['pubnet']
	   allyml['cluster_network'] = form.clnet.data
	   allyml['osd_objectstore'] = form.osdtype.data
	   allyml['radosgw_address'] = rgwip
	   with open('../ceph-ansible/group_vars/all.yml', 'w') as outfile:
    		yaml.dump(allyml, outfile, default_flow_style=False)
	   #edit osds.yml menggunakan pyyaml
           devices = form.device.data.split(',')
	   stream = open('../ceph-ansible/group_vars/osds.yml','r')
           osds = yaml.load(stream)
	   counter = 0
	   while counter < len(devices)-1:
		osds["lvm_volumes"][counter]["data"] = form.device.data
	    	if form.isjournal.data == False:
		     osds["lvm_volumes"][counter]["journal"] = form.device.data
	    	else:
		     osds["lvm_volumes"][counter]["journal"] = form.journal.data
	        counter = counter + 1  
	   with open('../ceph-ansible/group_vars/osds.yml', 'w') as outfile:
	 	yaml.dump(allyml, outfile, default_flow_style=False)
	   #edit hosts2 dengan seluruh IP yang diberikan
	   osd_ip = osdip(',')
	   mon_ip = monip(',')
	   file = open('/home/tasds/roseph/ceph-ansible/hosts2','w')
           file.write('[mons]\n')
	   for ip in mon_ip:
		file.write(ip+'\n')
	   file.write('\n')
	   file.write('[osds]\n')
           for ip in osd_ip:
                file.write(ip+'\n')
	   file.write('\n ')
	   file.write('[mgrs]\n')
           for ip in mon_ip:
                file.write(ip)
           file.write('\n ')
	   file.write('[mdss]\n')
           for ip in mon_ip:
                file.write(ip+'\n')
           file.write('\n ')
	   file.write('[rgws]\n')
	   file.write(rgwip)
	   file.close()
	   #jalankan bash skrip ansible
 	   bashCommand = 'ansible-playbook ../ceph-ansible/site.yml'
	   output = subprocess.check_output(['bash','-c', bashCommand])
	   return redirect('/')
    elif request.method == 'GET':
	if stream == '':
		return render_template('deploypolos.html', form=form,hosts=hosts)
	else:   
		return render_template('deploy.html', form=form, hosts=hosts)
	
@app.route('/Deploy/Addnode', methods = ['GET','POST'])
def addNode():
    form = addnode(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('adddeploy.html', form=form)
        else:
            host = dict()
	    hosts = []
	    stream = open('deploy.yml','r+')
	    if stream != '':	
	    	hosts = yaml.load(stream)
	    host['hostname'] = form.hostname.data
	    host['ip_addr'] = form.ip_addr.data
	    subnet = ipcalc.Network(form.ip_addr.data)
	    host['netaddr'] = subnet.network()
	    host['ismon'] = form.ismon.data
	    host['isosd'] = form.isosd.data
	    host['isrgw'] = form.isrgw.data
	    if stream != '':
	        hosts.append(host)
	    else:
		hosts=[host]
	    with open('deploy.yml', 'w+') as outfile:
		yaml.dump(hosts, outfile, default_flow_style=False)
            return redirect('/Deploy')
    if request.method == 'GET' :
	return render_template('adddeploy.html', form=form)

@app.route('/Deploy/Reset')
def deployreset():
    bashCommand = 'rm deploy.yml'
    output = subprocess.check_output(['bash','-c', bashCommand])
    bashCommand = 'touch deploy.yml'
    output = subprocess.check_output(['bash','-c', bashCommand])
    return redirect('/Deploy')

@app.route('/Deploy/Delete/<string:hostname>')
def deploydelete(hostname):
    stream = open('deploy.yml','r+')    
    hosts = yaml.load(stream)
    cari = []
    c = 0
    while c!=len(hosts):
	cari.append(hosts[c]['hostname'])
	c = c+1
    ind = cari.index(hostname)
    hosts.pop(ind)
    with open('deploy.yml', 'w+') as outfile:
        yaml.dump(hosts, outfile, default_flow_style=False)
    return redirect('/Deploy')


#Modul Purging
#Tujuan : Melakukan penghapusan terhadap sistem penyimpanan yang sudah ada
#Masukan : checkbox x2 dan 1 string konfirmasi
#Luaran  : laman dan sistem terhapus
@app.route('/Purge', methods = ['GET', 'POST'])
def purge():
    form = purgeform(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('purge.html', form=form)
	else:
	    if (form.yakin1.data and form.yakin2.data and (form.ireallymeanit.data == 'yes')):
	         bashCommand = 'ansible-playbook ../ceph-ansible/purge-cluster.yml -e "ireallymeanit=yes"'
           	 output = subprocess.check_output(['bash','-c', bashCommand])
		 return redirect('/')
    elif request.method == 'GET':
	 return render_template('purge.html', form=form)


#Modul Dashboard
#Tujuan : Melakukan penampilan data untuk memantau kondisi cluster secara umum
#Masukan : none
#Luaran  : laman (kondisi cluster, keterpakaian cluster)
@app.route('/Dashboard')
def index():
    r = requests.get('http://10.10.6.1:5000/api/v0.1/health.json')
    r1 = requests.get('http://10.10.6.1:5000/api/v0.1/fsid.json')
    r2 = requests.get('http://10.10.6.1:5000/api/v0.1/pg/stat.json')
    pgstat = json.loads(r2.text)
    datapersen =math.ceil((pgstat['output']['raw_bytes_used'])/(pgstat['output']['raw_bytes_avail'])*100)
    return render_template('home.html',datum=datapersen,data =json.loads(r.text),data1=json.loads(r1.text),headers=headers)

#Modul Daftar Pengguna
#Tujuan : Melakukan penampilan data untuk memantau pengguna dan kapabilitasnya
#Masukan : none
#Luaran  : laman (ID, Keyring, Kapabilitas)
@app.route('/AddUser')
def adduser():
    r = requests.get('http://10.10.6.1:5000/api/v0.1/auth/list.json')
    return render_template('adduser.html', data =json.loads(r.text),headers=headers)

#Modul Hapus Pengguna
#Tujuan : Melakukan penghapusan pengguna tertentu
#Masukan : Nama pengguna
#Luaran  : none (updated db)
@app.route('/AddUser/DelUser/<string:entity>', methods = ['GET','PUT'])
def deluser(entity):
    requests.put('http://10.10.6.1:5000/api/v0.1/auth/del', params={"entity":entity},headers=headers)
    return redirect('/AddUser')

#Modul Tambah Pengguna
#Tujuan : Melakukan penambahan pengguna
#Masukan : Nama pengguna dan kapabilitas
#Luaran  : laman (updated db)
@app.route('/AddUser/form', methods = ['GET','POST','PUT'])
def adduserform():
    form = BuatUser(request.form)
    r = requests.get('http://10.10.6.1:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    form.pool.choices = [(pool,pool) for pool in pools]   
    if request.method == 'POST':
        if form.validate() == False:
            flash('Isi seluruhnya')
            return render_template('form.html', form=form)
        else:
            requests.put('http://10.10.6.1:5000/api/v0.1/auth/get-or-create',
                params={"entity":"client."+form.userID.data, "caps":[ 
                PilihCapsMon(form.MONr.data,form.MONw.data,form.MONx.data),
                PilihCapsOsd(form.OSDr.data,form.OSDw.data,form.OSDx.data, form.pool.data),
                PilihCapsMds(form.MDSr.data,form.MDSw.data,form.MDSx.data)]},headers=headers)
            return redirect('/AddUser')
    elif request.method == 'GET':
        return render_template('form.html', form=form)

#Modul Sunting Pengguna
#Tujuan : Melakukan penyuntingan pengguna yang telah ada
#Masukan : Nama pengguna dan kapabilitas
#Luaran  : laman (updated db)
@app.route('/AddUser/EditUser/<string:entity>', methods = ['GET','POST','PUT'])
def edituser(entity):
    form = BuatUser(request.form)
    form.userID.data = entity
    r = requests.get('http://10.10.6.1:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    form.pool.choices = [(pool,pool) for pool in pools]

    if request.method == 'POST':
        if form.validate() == False:
            flash('Isi seluruhnya')
            return render_template('formedit.html', form=form, entity=entity)
        else:
            requests.put('http://10.10.6.1:5000/api/v0.1/auth/caps',
                params={"entity":form.userID.data, "caps":[
                PilihCapsMon(form.MONr.data,form.MONw.data,form.MONx.data),
                PilihCapsOsd(form.OSDr.data,form.OSDw.data,form.OSDx.data,form.pool.data),
                PilihCapsMds(form.MDSr.data,form.MDSw.data,form.MDSx.data)]},headers=headers)
            return redirect('/AddUser')
    elif request.method == 'GET':
        return render_template('formedit.html', form=form, entity=entity)

#Modul Daftar Volume
#Tujuan : Melakukan penampilan data untuk memantau pool yang ada di sistem serta block volume yang ada di pool
#Masukan : None
#Luaran  : Laman (Pool Id, pool name, recovery rate, client i/o rate, recovery, Image name, capacity,dan pool source)
@app.route('/VolumeList',methods = ['GET','POST'])
def volumelist():
    r = requests.get('http://10.10.6.1:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    images = []
    list_dict = []
    dict = {}
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    for pool in pools:
        poolimages = (list_image(pool))
        if poolimages != []:
            dict['namapool'] = pool
        for i in poolimages:
	    dict['namaimage'] = i
	    haha  = image_info(pool,i)
	    dict['size'] = haha['size']/1024**3
            images.append(i)
	    list_dict.append(dict.copy())
    return render_template('addvolume.html', data=json.loads(r.text), dict=list_dict)

#Modul Tambah Pool
#Tujuan : Melakukan penambahan pool baru
#Masukan : Nama pool, PG number, dan PGP number
#Luaran  : laman (updated db)
@app.route('/VolumeList/formpool',methods=['GET','POST','PUT'])
def formpool():
    form = BuatPool(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('formpool.html', form=form)

        else:
            requests.put('http://10.10.6.1:5000/api/v0.1/osd/pool/create',headers=headers, params = {'pool':form.namaPool.data, 'pg_num':form.PGnum.data, 'pgp_num':form.PGPnum.data})
	    return redirect('/VolumeList')
    elif request.method == 'GET':
   	 return render_template('formpool.html', form=form)	

#Modul Tambah Image
#Tujuan : Melakukan penambahan block image baru
#Masukan : Nama pool, nama image, dan kapasitas
#Luaran  : laman (updated db)
@app.route('/VolumeList/formimage',methods=['GET','POST','PUT'])
def formimage():
    form = BuatImage(request.form)
    r = requests.get('http://10.10.6.1:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    form.namaPool.choices = [(pool,pool) for pool in pools]
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('formimage.html', form=form)
        else:
            newImage(form.namaPool.data, form.namaImage.data, form.kapasitas.data)
            return redirect('/VolumeList')
    if request.method == 'GET' :
        return render_template('formimage.html', form=form)

#Modul Sunting Pool
#Tujuan : Melakukan penyuntingan PG dan PGP number dari pool yang ada
#Masukan : Nama pool, PG number, dan PGP number
#Luaran  : laman (updated db)
@app.route('/VolumeList/EditPool/<string:poolname>', methods = ['GET','PUT','POST'])
def editpool(poolname):
    form = BuatPool(request.form)
    form.namaPool.data = poolname
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('editpool.html',form=form, poolname=poolname)
        else:
            requests.put('http://10.10.6.1:5000/api/v0.1/osd/pool/set',params={"pool":form.namaPool.data, "var":"pg_num", "val":form.PGnum.data}, headers=headers)
            requests.put('http://10.10.6.1:5000/api/v0.1/osd/pool/set',params={"pool":form.namaPool.data, "var":"pgp_num", "val":form.PGPnum.data}, headers=headers)
            return redirect('/VolumeList')
    elif request.method == 'GET':
        return render_template('editpool.html', form=form, poolname=poolname)

#Modul Hapus Pool
#Tujuan : Melakukan penghapusan ke pool yang ada 
#Masukan : Nama pool
#Luaran : none (updated db)
@app.route('/VolumeList/DelPool/<string:poolname>', methods = ['GET','PUT'])
def delpool(poolname):
    requests.put('http://10.10.6.1:5000/api/v0.1/osd/pool/delete', params={"pool":poolname,"pool2":poolname, "sure":"--yes-i-really-really-mean-it"},headers=headers)
    return redirect('/VolumeList')

#Modul Sunting Image
#Tujuan : Melakukan penyuntingan dari image yang sudah ada
#Masukan : nama image, kapasitas dan nama pool tempat adanya image tersebut
#Luaran  : laman (updated db)
@app.route('/VolumeList/EditVolume/<string:namaimage>/<string:namapool>', methods=['GET','POST'])
def editblock(namaimage,namapool):
    form = BuatImage(request.form)
    form.namaImage.data = namaimage
    if request.method == 'POST':
        editImage(namapool, namaimage, form.kapasitas.data)
        return redirect('/VolumeList')
    elif request.method == 'GET':
        return render_template('formeditimage.html', form=form,namaimage=namaimage,namapool=namapool)

#Modul Hapus Image
#Tujuan : Melakukan penghapusan dari image yang sudah ada
#Masukan : nama image dan nama pool tempat adanya image tersebut
#Luaran  : none (updated db)
@app.route('/VolumeList/DelVolume/<string:namaimage>/<string:namapool>', methods=['GET'])
def delblock(namapool,namaimage):
    deleteImage(namapool,namaimage)
    return redirect('/VolumeList')

#Modul Konfigurasi Sistem
#Tujuan : Melakukan tampilan kondisi daemon dalam kluster
#Masukan : none
#Luaran  : Laman (tabel OSD[name, id, class] dan tabel MON[name, rank, address])
@app.route('/Konfigurasi', methods = ['GET','POST','PUT'])
def konfig():
    r1=requests.get('http://10.10.6.1:5000/api/v0.1/mon_status.json',headers=headers)
    data = json.loads(r1.text)
    for list in data["output"]["monmap"]["mons"]:
	ip = list["addr"].split(":")
	list["addr"] = ip[0]
    r2=requests.get('http://10.10.6.1:5000/api/v0.1/mds/stat.json',headers=headers)
    r3=requests.get('http://10.10.6.1:5000/api/v0.1/osd/crush/dump.json', headers=headers)
    return render_template('konfig.html',data =data,datamds=json.loads(r2.text), dataosd=json.loads(r3.text))

#Modul Hapus OSD
#Tujuan : Melakukan penghapusan OSD yang telah ada
#Masukan : nama OSD
#Luaran  : none (updated db)
#Keterangan : OSD yang telah dihapus tidak dapat langsung digunakan kembali 
@app.route('/Konfigurasi/DeleteOSD/<string:namaosd>')
def delOSD(namaosd):
    bashCommand = 'ansible-playbook -e "ireallymeanit=yes osd_to_kill={}" ../ceph-ansible/shrink-osd.yml'.format(namaosd)
    output = subprocess.check_output(['bash','-c', bashCommand])   
    return redirect('/Konfigurasi')

#Modul Tambah OSD
#Tujuan : Melakukan penambahan OSD baru (scaling up)
#Masukan : Alamat ip osd, alamat devais, alamat jurnal jika ada
#Luaran  : laman (updated db)
@app.route('/Konfigurasi/TambahOSD', methods = ['GET','POST'])
def addOSD():
    form = TambahOSD(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('addosd.html',form=form)
        else:
            #daftarkan IP node baru di /etc/ansible/hosts
	    file = open('/home/tasds/roseph/ceph-ansible/hosts2','r')
	    lines = file.readlines()
	    file.close()
	    file = open('/home/tasds/roseph/ceph-ansible/hosts2','w')
	    count = 0
	    while (lines[count] != "[osds]\n"):
		file.write(lines[count])
		count = count +1
	    file.write("[osds]\n")
	    file.write(form.ip_addr.data)
	    file.close()
	    #buka osds.yml pakai pyyaml
	    stream = open('/home/tasds/roseph/ceph-ansible/group_vars/osds.yml','r')
	    osds   = yaml.load(stream)
	    osds["lvm_volumes"][0]["data"] = form.device.data
	    if form.isjournal.data == False:
		osds["lvm_volumes"][0]["journal"] = form.device.data
	    else:
		osds["lvm_volumes"][0]["journal"] = form.journal.data
	    stream = open('/home/tasds/roseph/ceph-ansible/group_vars/osds.yml','w')
	    yaml.dump(osds,stream)
            #jalankan bash shellnya
	    bashCommand = "ansible-playbook /home/tasds/roseph/ceph-ansible/osd-configure.yml"
	    output = subprocess.check_output(['bash','-c', bashCommand])
            return redirect('/Konfigurasi')
    elif request.method == 'GET':
        return render_template('addosd.html', form=form)

#Modul Hapus Monitor
#Tujuan : Melakukan penghapusan dari monitor yang sudah ada
#Masukan : nama monitor 
#Luaran  : none (updated db)
@app.route('/Konfigurasi/DelMon/<string:namamon>')
def DelMon(namamon):
    bashCommand = 'ansible-playbook -e "ireallymeanit=yes mon_to_kill={}" ../ceph-ansible/shrink-mon.yml'.format(namamon)
    output = subprocess.check_output(['bash','-c', bashCommand])
    return redirect('/Konfigurasi')

#Modul Penambahan Monitor
#Tujuan : Melakukan penambahan monitor baru
#Masukan : alamat ip
#Luaran  : laman (updated db)
@app.route('/Konfigurasi/AddMon', methods = ['GET', 'POST'])
def AddMon():
    form = TambahOSD(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('addmon.html',form=form)
        else:
            #daftarkan IP node baru di /etc/ansible/hosts
            file = open('/home/tasds/roseph/ceph-ansible/hosts2','r')
            lines = file.readlines()
            file.close()
            file = open('/home/tasds/roseph/ceph-ansible/hosts2','w')
            for line in lines:
		if line != form.ip_addr.data:
			file.write(line)
	    file.close()
	    #jalankan bash ansible
	    bashCommand = 'ansible-playbook ../ceph-ansible/site-mon.yml'
	    output = subprocess.check_output(['bash','-c', bashCommand])
	    return redirect('/Konfigurasi')
    if request.method == 'GET':
	return render_template('addmon.html',form=form)

#Modul Ceph.conf
#Tujuan : Melakukan pengiriman ceph.conf dari sistem agar dapat didownload
#Masukan : none
#Luaran  : ceph.conf
@app.route('/Kirim', methods = ['GET','POST'])
def cephconf():
    return send_file('/etc/ceph/ceph.conf',attachment_filename='ceph.conf')

#Modul kirim keyring
#Tujuan : Melakukan pengiriman keyringpengguna dari sistem agar dapat didownload
#Masukan : nama pengguna
#Luaran  : ceph.conf
@app.route('/KirimContohKeyring/<string:client>/<string:keyring>', methods = ['GET', 'POST'])
def clientkeyring(client,keyring):
    file = open('/home/tasds/{}.keyring'.format(client),'w+')
    file.write('[{}.keyring]]\n'.format(client))
    file.write('        key = {}'.format(keyring))
    file.close()
    return send_file('/home/tasds/{}.keyring'.format(client))


if __name__=='__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)
