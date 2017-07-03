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

### Test Case Introduction
+ TestCase1

1)、用户user1创建桶test1

2)、subuser1向桶test1中上传对象1

3)、subuser2创建桶test2

预期结果:

1)、查看user1的usage信息，会显示user1 , subuser和subuser1所有操作的create_bucket, put_obj

2)、查看subuser1的usage信息，只会显示其put_obj

3)、查看subuser2的usage信息，只会显示其create_bucket


+ TestCase2

1)、subuser1创建桶test1

预期结果:

查看subuser1的usage信息，只会显示create_bucket。查看用户user1的usage信息，也会显示create_bucket

2)、subuser2向桶test1中上传对象1

预期结果:

查看subuser2的usage信息，只会显示其put_obj信息。查看user1的信息，会显示create_bucket和put_obj。查看subuser1的usage的信息，只会显示create_bucket

3)、用户user1向桶test1中上传对象2

预期结果:

查看用户user1的usage信息，会显示create_bucket，对象1和对象2的put_obj；查看subuser1只显示create_bucket；查看subuser2只会显示对象1的put_obj

4)、暂不删除数据和用户


+ TestCase3

1)、用户user1通过test1下载对象2

2)、用户user1通过test1下载对象1

预期结果:

user1的usage信息，先后会增加对象2和对象1的get_obj，其它用户的usage信息不变

3)、subuser1通过test1下载对象1

4)、subuser1通过test1下载对象2

预期结果:

subuser1的usage信息，先后会增加对象1和对象2的get_obj；user1的usage信息，先后对象1和对象2的get_obj会增加一次，其它用户的usage信息不变

5)、subuser2通过test1下载对象1

6)、subuser2通过test1下载对象2

7)、暂不删除数据和用户

预期结果:

subuser2的usage信息，先后会增加对象1和对象2的get_obj；user1的usage信息，先后对象1和对象2的get_obj会增加一次，其它用户的usage信息不变


+ TestCase4

1)、用户user1删除对象2

预期结果:

user1的usage信息，会增加对象2的delete_obj，其它的用户的usage信息不变

2)、 subuser2删除对象1

预期结果:

subuser2的usage信息，会增加对象1的delete_obj；user1的usage信息，会增加对象1的delete_obj，其它的用户的usage信息不变

3)、用户user1删除test1  

删除第三个测试用例中的用户和数据

user1的usage信息，增加桶test1的delete_bucket信息，其它的子账号不变


+ TestCase5

1)、subuser1创建桶test1

预期结果:

查看subuser1的usage信息，只会显示create_bucket。查看用户user1的usage信息，也会显示create_bucket

2)、subuser2创建桶test2

预期结果:

查看subuser2的usage信息，会显示test2的create_bucket信息；查看用户user1的usage信息，会显示test1和test2的create_bucket；查看subuser1只显示test1的create_bucket

3)、subuser1向桶test2中上传对象1

预期结果:

查看subuser2的usage信息，会显示test2的create_bucket信息；查看用户user1的usage信息，会显示test1和test2的create_bucket，对象1的put_obj；查看subuser1会显示test1的create_bucket，对象1的put_obj

4)、用户user1创建桶test3  

5)、用户user1向桶test3中上传对象2  

暂时不删除用户和数据  

预期结果:

查看user1的usage信息，先会增加test3的creat_bucket，再增加对象3的put_obj，其它的子账号usage信息不变


+ TestCase6

1)、用户user1下载对象2

预期结果:

user1的usage信息，会增加对象2的get_obj，其它用户的usage信息不变

2)、subuser1下载对象1

3)、subuser1下载对象2

预期结果:

subuser1的usage信息，先后会增加对象1和对象2的get_obj；user1的usage信息，先后对象1和对象2的get_obj会增加一次，其它用户的usage信息不变

4)、subuser2下载对象1

5)、subuser2下载对象2

暂时不删除用户和数据

预期结果:

subuser2的usage信息，先后会增加对象1和对象2的get_obj；user1的usage信息，先后对象1和对象2的get_obj会增加一次，其它用户的usage信息不变


+ TestCase7

1)、用户user1 list test1

2)、用户user1 list test2

3)、用户user1 list test3

预期结果:

user1的usage信息，先后会增加桶test1，test2，test3的list_bukcet，其它用户的usage信息不变

4)、subuser1 list test1

5)、subuser1 list test2

6)、subuser1 list test3

预期结果:

subuser1的usage信息，先后会增加桶test1,test2,test3的list_bukcet；user1的usage信息，先后会增加桶test1,test2,test3的list_bukcet，其它用户的usage信息不变

7)、subuser2 list test1

8)、subuser2 list test2

9)、subuser2 list test3

预期结果:

subuser2的usage信息，先后会增加桶test1,test2,test3的list_bukcet；user1的usage信息，先后会增加桶test1,test2,test3的list_bukcet，其它用户的usage信息不变


+ TestCase8

1)、用户user1删除对象2

预期结果:

user1的usage信息，会增加对象2的delete_obj，其它的用户的usage信息不变

2)、subuser1删除对象1

预期结果:

subuser1的usage信息，会增加对象1的delete_obj；user1的usage信息，会增加对象1的delete_obj，其它的用户的usage信息不变

3)、subuser2删除桶test2

预期结果:

subuser2的usage信息，会增加桶test2的delete_bucket；user1的usage信息，会增加桶test2的delete_bucket，其它的用户的usage信息不变

4)、subuser1删除桶test1

预期结果:

subuser1的usage信息，会增加桶test1的delete_bucket；user1的usage信息，会增加桶test1的delete_bucket，其它的用户的usage信息不变

5)、用户user1删除桶test3

清除用户和数据

user1的usage信息，增加桶test3的delete_bucket信息，其它的子账号不变


+ TestCase9

1)、用户user1创建桶test1

预期结果:

查看用户user1的usage信息，会显示test1的create_bucket

2)、subuser1创建桶test2

预期结果:

查看subuser1的usage信息，会显示test2的create_bucket。查看用户user1的usage信息，也会显示test2的create_bucket

3)、用户user1向桶test2中上传对象1

预期结果:

查看用户user1的usage信息，会显示对象1的put_obj；其它子账号usage信息不变。

4)、subuser1向桶test1中上传对象2

预期结果:

查看subuser1的usage信息，会显示对象2的put_obj信息。查看user1的信息，会显示对象2的put_obj。其它子账号usage信息不变。

5)、subuser1向桶test2中上传对象3

暂时不删除用户和数据

预期结果:

查看subuser1的usage信息，会显示对象3的put_obj信息。查看user1的信息，会显示对象3的put_obj。其它子账号usage信息不变。


+ TestCase10

1)、用户user1下载对象3

预期结果:

user1的usage信息，会增加对象3的get_obj，其它用户的usage信息不变

2)、subuser1下载对象1

3)、subuser1下载对象2

4)、subuser1下载对象3

预期结果:

subuser1的usage信息，先后会增加对象1，对象2，对象3的get_obj；user1的usage信息，先后对象1，对象2和对象3的get_obj会增加一次，其它用户的usage信息不变


+ TestCase11

1)、用户user1 list test1

2)、用户user1 list test2

预期结果:

user1的usage信息，先后会增加桶test1，test2的list_bucket，其它用户的usage信息不变

3)、subuser1 list test1

4)、subuser1 list test2

预期结果:

subuser1的usage信息，先后会增加桶test1，test2的list_bucket；user1的usage信息，先后会增加桶test1，test2的list_bucket，其它用户的usage信息不变


+ TestCase12

1)、用户user1删除对象1

预期结果:

user1的usage信息，增加对象1的delete_obj信息，其它的子账号不变

2)、subuser1删除对象2

预期结果:

subuser1的usage信息，会增加对象2的delete_obj；user1的usage信息，会增加对象2的delete_obj，其它的用户的usage信息不变

3)、用户user1删除test1

预期结果:

user1的usage信息，增加桶test1的delete_bucket信息，其它的子账号不变

4)、subuser1删除对象3

预期结果:

subuser1的usage信息，会增加对象3的delete_obj；user1的usage信息，会增加对象3的delete_obj，其他用户的usage信息不变

5)、subuser1删除test2

删除用户及其数据

预期结果:

subuser1的usage信息，会增加桶test2的delete_bucket；user1的usage信息，会增加桶test2的delete_bucket，其它的用户的usage信息不变


+ TestCase13

1)、用户user1创建桶test1

2)、用户user1上传对象1到桶test1

预期结果:

user1的usage信息，先后会增加桶test1的create_bucket和对象1的put_obj，其它用户的usage信息不变

3)、用户user2创建桶test01

4)、用户user2上传对象01到桶test01

预期结果:

user2的usage信息，先后会增加桶test01的create_bucket和对象01的put_obj，其它用户的usage信息不变

5)、subuser1创建桶test2

6)、subuser1上传对象2到test2

预期结果:

subuser1的usage信息，先后会增加桶test2的create_bucket和对象2的put_obj；user1的usage信息，先后桶test2的create_bucket和对象2的put_obj会增加一次，其它用户的usage信息不变

7)、subu01创建桶test02

8)、subu01上传对象02到test02

预期结果:

subu01的usage信息，先后会增加桶test02的create_bucket和对象02的put_obj；user2的usage信息，先后桶test02的create_bucket和对象02的put_obj会增加一次，其它用户的usage信息不变


+ TestCase14

1)、user1下载对象1

预期结果:

user1的usage信息，会增加对象1的get_obj，其它用户的usage信息不变

2)、subuser1下载对象2

预期结果:

subuser1的usage信息，会增加对象2的get_obj；user1的usage信息，对象2的get_obj会增加一次，其它用户的usage信息不变

3)、user2下载对象01

预期结果:

user2的usage信息，会增加对象01的get_obj，其它用户的usage信息不变

4)、subu01下载对象02

预期结果:

subu01的usage信息，会增加对象02的get_obj；user2的usage信息，对象02的get_obj会增加一次，其它用户的usage信息不变


+ TestCase15

1)、user1 list桶test1

预期结果:

user1的usage信息，会增加桶test1的list_bucket，其它用户的usage信息不变

2)、subuser1 list桶test2

预期结果:

subuser1的usage信息，会增加桶test2的list_bucket；user1的usage信息，会增加桶test2的list_bucket，其它用户的usage信息不变

3)、user2 list桶test01

预期结果:

user2的usage信息，会增加桶test01的list_bucket，其它用户的usage信息不变

4)、subu01 list桶test02

预期结果:

subu01的usage信息，会增加桶test02的list_bucket；user2的usage信息，会增加桶test02的list_bucket，其它用户的usage信息不变


+ TestCase16

1)、user1删除对象1

2)、user1删除桶test1

预期结果:

user1的usage信息，先后会增加对象1的delete_obj和桶test1的delete_bucket，其它的用户的usage信息不变

3)、subuser1删除对象2

4)、subuser1删除桶test2

预期结果:

subuser1的usage信息，先后会增加对象2的delete_obj和桶test2的delete_bucket；user1的usage信息，会增加对象2的delete_obj和桶test2的delete_bucket，其它的用户的usage信息不变

5)、user2删除对象01

6)、user2删除桶test01

预期结果:

user2的usage信息，先后会增加对象01的delete_obj和桶test01的delete_bucket，其它的用户的usage信息不变

7)、subu01删除对象02

8)、subu01删除桶test02

预期结果:

subu01的usage信息，先后会增加对象02的delete_obj和桶test02的delete_bucket；user2的usage信息，会增加对象02的delete_obj和桶test02的delete_bucket，其它的用户的usage信息不变


+ TestCase17

1)、user1创建存储桶test1

2)、subuser1上传对象1到test1

3)、subuser2创建存储桶test2

预期结果:

user1的usage信息，先后会增加桶test1的create_bucket、对象1的put_obj、test2的create_bucket；subuser1的usage信息，会增加对象1的put_obj；subuser2的usage信息，会增加桶test2的create_bucket；

4)、删除subuser1

预期结果:

user1的usage信息和subuser2的usage信息保持不变，不会受到影响

5)、删除subuser2

预期结果:

user1的usage信息保持不变，不会受到影响


+ TestCase18

1)、user1下创建1000个子账户，user1创建存储桶test1

预期结果:

user1的usage信息，会增加桶test1的create_bucket。所有子账户的usage信息不变为空。

2)、subuser1创建存储桶test2

预期结果:

subuser1的usage信息，会增加桶test2的create_bucket；user1的usage信息，会增加test2的create_bucket；其他子账户的usage信息不变。

3)、subuser666上传对象1到test2

预期结果:

subuser666的usage信息，会增加对象1的put_obj；user1的usage信息，会增加对象1的put_obj；其他子账户的usage信息不变。

4)、user2创建存储桶test3

预期结果:

user2的usage信息，会增加桶test3的create_bucket；user1及其子账户的usage信息不受影响，保持不变。


+ TestCase19

usage show --categories参数对操作类型的过滤


+ TestCase20

1)、user1创建存储桶test1

2)、subuser1上传对象1到test1

3)、subuser2创建存储桶test2

预期结果:

user1的usage信息，先后会增加桶test1的create_bucket、对象1的put_obj、test2的create_bucket；subuser1的usage信息，会增加对象1的put_obj；subuser2的usage信息，会增加桶test2的create_bucket；

4)、删除子账户subuser1，查看账户user1及子账户subuser1和subuser2的usage信息

预期结果:

删除子账户subuser1后，user1、subuser1、subuser2的usage信息不变。

5)、删除子账户subuser2，查看账户user1及子账户subuser1和subuser2的usage信息

预期结果:

删除子账户subuser2后，user1、subuser1、subuser2的usage信息不变。

6)、创建同名子账户subuser1，再查看user1、subuser1、subuser2的usage信息

预期结果:

创建同名的子账户subuser1后，子账户subuser1的usage信息并不重置，而是继续保存之前的subuser1的usage信息

7)、删除账户user1

预期结果:

在没有进行usage trim操作的情况下，user1及其对应的子账户subuser1、subuser2的usage信息并不会被清除。

8)、创建同名用户user1

预期结果:

用户user1的usage信息并不会被清除重置，而是继续保存了之前的user1的usage信息。


+ TestCase21

1)、user1创建存储桶test1

2)、subuser1上传对象1到test1

3)、subuser2创建存储桶test2

4)、user2创建存储桶test01

5)、user2上传对象2到存储桶test01

预期结果:

user1的usage信息，先后会增加桶test1的create_bucket、对象1的put_obj、test2的create_bucket；subuser1的usage信息，会增加对象1的put_obj；subuser2的usage信息，会增加桶test2的create_bucket；user2的usage信息，先后会增加桶test01的create_bucket、对象2的put_obj。

6)、user1设置桶test1的acl来授权user2对test1具有写权限

7)、user2上传对象3到桶test1中

预期结果:

user1的usage信息，先后会增加桶test1的get_acls和put_acls操作，对象3的put_obj操作；user2的usage信息保持不变；user1的子账户subuser1和subuser2的usage信息保持不变；

8)、递归删除桶test1

预期结果:

user1的usage信息，先后增加了桶test1的list_bucket、multi_object_delete、delete_bucket操作；user2的usage信息保持不变；user1的子账户subuser1和subuser2的usage信息保持不变；


+ TestCase22

1)、user1创建存储桶test1

2)、subuser1上传对象1到test1

3)、subuser2创建存储桶test2

4)、user2创建存储桶test01

5)、user2的子账户subuser2上传对象2到存储桶test01

预期结果:

user1的usage信息，先后会增加桶test1的create_bucket、对象1的put_obj、test2的create_bucket；subuser1的usage信息，会增加对象1的put_obj；subuser2的usage信息，会增加桶test2的create_bucket；user2的usage信息，先后会增加桶test01的create_bucket、对象2的put_obj；user2的子账户subuser2会增加对象2的put_obj操作。

6)、user1设置桶test1的acl来授权user2对test1具有读写权限

7)、user2上传对象3到test1

8)、user2的子账户subuser2从桶test1中获取对象3

9)、user2的子账户subuser3 list test1

预期结果:

user1的usage信息，先后会增加桶test1的put_acls和get_acls操作两次、对象3的put_obj操作一次、对象3的get_obj操作一次；user2的子账户subuser2的usage信息会增加对象3的get_obj操作一次；user2的子账户subuser3会增加桶test1的list_bucket操作一次；其他用户的usage信息保持不变；

10)、删除user1的子账户subuser2，查看各用户及子账户的usage信息

预期结果:

各账户和子账户的usage信息均保持不变

11)、user2的子账户subuser2上传对象4到桶test2中

预期结果:

user1的usage信息，会增加对象4的put_obj操作，但successful_op为0；user2的subuser2的usage信息，会增加对象4的put_obj操作，但successful_op为0；其他账户和子账户的usage信息保持不变。


+ TestCase23

1)、user1创建存储桶test1

2)、subuser1上传对象1到test1

3)、subuser2 list test1

预期结果:

user1的usage信息，先后会增加桶test1的create_bucket、对象1的put_obj、test1的list_bucket；subuser1的usage信息，会增加对象1的put_obj；subuser2的usage信息，会增加桶test1的list_bucket；

4)、user1上传对象2到桶test21331

预期结果:

user1的usage信息，会增加对非法访问的记录，即非法桶"-"中，会增加对象2的put_obj操作，successful_op为0；其他账户和子账户的usage信息保持不变；

5)、subuser2 list test77

预期结果:

user1的usage信息，会增加对非法桶"-"的list_bucket操作记录，successful_op为0；subuser2的usage信息会增加对非法桶"-"的list_bucket操作记录，successful_op为0

6)、subuser1上传非法对象"dagfdagad"到桶test1中

预期结果:

因为对象"dagfdagad"并不存在，所以s3cmd压根不会向RGW发送请求，所以所有的账户和子账户的usage信息保持不变。
