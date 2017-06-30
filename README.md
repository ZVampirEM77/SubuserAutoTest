# SubuserAutoTest
## auto_test.py
+ 需要对当前所要测试的Ceph的版本进行设置，以决定如何调用radosgw-admin

因为主要的分水岭是从K版本开始的，所以当前脚本中的ceph_version可以设置为:

ceph_version = '>=K'

or

ceph_version = '\<K'


+ 同时需要对脚本中的ceph_path进行设置:

ceph/build --> K版本之后的版本

ceph/src --> K版本之前的版本

