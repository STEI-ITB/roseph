import rados, rbd

def PilihCapsMon(r,w,x):
    if r == True and w ==True and x == True:
        return "mon", "allow rwx"
    elif r == True and w == True and x == False:
        return "mon", "allow rw"
    elif r == True and w == False and x == True:
        return "mon", "allow rx"
    elif r == True and w == False and x == False:
        return "mon", "allow r"
    elif r == False and w == True and x == True:
        return "mon", "allow wx"
    elif r == False and w == False and x == True:
        return "mon", "allow x"
    elif r == False and w == True and x == False:
        return "mon", "allow w"
    elif r == False and w == False and x == False:
        return None

def PilihCapsOsd(r,w,x,pool):
    if r == True and w ==True and x == True:
        return "osd", "allow rwx pool ={}".format(pool)
    elif r == True and w == True and x == False:
        return "osd", "allow rw pool={}".format(pool)
    elif r == True and w == False and x == True:
        return "osd", "allow rx pool ={}".format(pool)
    elif r == True and w == False and x == False:
        return "osd", "allow r pool={}".format(pool)
    elif r == False and w == True and x == True:
        return "osd", "allow wx pool={}".format(pool)
    elif r == False and w == False and x == True:
        return "osd", "allow x pool={}".format(pool)
    elif r == False and w == True and x == False:
        return "osd", "allow w pool={}".format(pool)
    elif r == False and w == False and x == False:
        return None

def PilihCapsMds(r,w,x):
    if r == True and w ==True and x == True:
        return "mds", "allow rwx"
    elif r == True and w == True and x == False:
        return "mds", "allow rw"
    elif r == True and w == False and x == True:
        return "mds", "allow rx"
    elif r == True and w == False and x == False:
        return "mds", "allow r"
    elif r == False and w == True and x == True:
        return "mds", "allow wx"
    elif r == False and w == False and x == True:
        return "mds", "allow x"
    elif r == False and w == True and x == False:
        return "mds", "allow w"
    elif r == False and w == False and x == False:
        return None

def list_image(pool_name):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
    cluster.connect()
    try:
        ioctx = cluster.open_ioctx(pool_name)
        rbd_ins = rbd.RBD()
        listimage = rbd_ins.list(ioctx)
    finally:
        cluster.shutdown()
    return listimage


def image_info(pool_name,image_name):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf') 
    cluster.connect()
    try:
        ioctx = cluster.open_ioctx(pool_name)
        image = rbd.Image(ioctx,image_name )
        try:
           imagestat = image.stat()
        finally:
           image.close()
    finally:
        cluster.shutdown()
    return imagestat

def newPool(pool_name):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
    cluster.connect()
    try:
        cluster.create_pool(pool_name)
    finally:
        cluster.shutdown()
    return None

def newImage(pool_name, image_name, size_in_gb):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
    cluster.connect()
    try:
        ioctx = cluster.open_ioctx(pool_name)
        try:
            rbd_inst = rbd.RBD()
            size = size_in_gb * 1024**3  # 4 GiB
            rbd_inst.create(ioctx, image_name, size)
        finally:
            ioctx.close()
    finally:
        cluster.shutdown()
    return None

def deleteImage(pool_name,image_name):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
    cluster.connect()
    try:
        ioctx = cluster.open_ioctx(pool_name)
        try:
            rbd_inst=rbd.RBD()
	    rbd_inst.remove(ioctx,image_name)
        finally:
            ioctx.close()
    finally:
        cluster.shutdown()
    return None

def editImage(pool_name,image_name, size):
    cluster = rados.Rados(conffile='/etc/ceph/ceph.conf')
    cluster.connect()
    try:
        ioctx = cluster.open_ioctx(pool_name)
        try:
            image = rbd.Image(ioctx,image_name)
            image.resize(size*1024**3)
        finally:
	    image.close()
    finally:
	ioctx.close()
        cluster.shutdown()
    return None

