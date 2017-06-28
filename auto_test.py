'''
By Enming Zhang

Email: enming.zhang@umcloud.com

2017-06-27
'''

import sys, os, json
import time
import argparse
import subprocess

ceph_path = "../ceph/build/"
py_dir = os.getcwd()

def exec_command(command):
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    p.communicate()
    
def exec_command_with_return(command):
    return subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

def ok_display(content):
    return "[\033[1;;32m%s\033[0m]" % (content)

def fail_display(content):
    return "[\033[1;;41m%s\033[0m]" % (content)

def get_user_name(user_dic):
    user_name = ""
    if "subuser" in user_dic:
        user_name = user_dic["user"] + ":" + user_dic["subuser"]
    else:
        user_name = user_dic["user"]
    return user_name

def parse_response_content(res_content):
    user_dict = {}
    for user_info in res_content["entries"]:
        user = get_user_name(user_info)
        user_dict[user] = {}
	for bucket in user_info["buckets"]:
	    user_dict[user][bucket["bucket"]] = {}
            user_dict[user][bucket["bucket"]]["categories"] = {}
	    for category in bucket["categories"]:
		user_dict[user][bucket["bucket"]]["categories"][category["category"]] = {}
                user_dict[user][bucket["bucket"]]["categories"][category["category"]]["ops"] = category["ops"]
                user_dict[user][bucket["bucket"]]["categories"][category["category"]]["successful_ops"] = category["successful_ops"]
    return user_dict

def verify_show_response_msg(req_command, expect_dict):
    usage_log = exec_command_with_return(req_command)	 
    data = json.load(usage_log)
    result = True
    user_dict = {}

    if len(data["entries"]) == expect_dict["entries_size"] and len(data["summary"]) == expect_dict["entries_size"]:
        if len(data["entries"]) != 0:
	    user_dict = parse_response_content(data)
	    for user_info in data["entries"]:
                user = get_user_name(user_info)  
	        if user_dict[user] != expect_dict[user]:
                    print data
		    print '---------------------'
		    print user_dict[user]
		    print '+++++++++++++++++++++'
		    print expect_dict
		    result = False
	else:
            result = True
    else:
	print data
	result = False

    return result

class TestCase1(object):
    def prepare(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin user create --uid=user1 --access-key=user1 --secret-key=user1 --display-name="user1"')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser1 --access=full --access-key=subuser1 --secret-key=subuser1')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser2 --access=full --access-key=subuser2 --secret-key=subuser2')
        os.chdir(py_dir)
	exec_command('s3cmd -c user1.s3cfg mb s3://test1')
        exec_command('s3cmd -c subuser1.s3cfg put user1.s3cfg s3://test1')
        exec_command('s3cmd -c subuser2.s3cfg mb s3://test2') 
        time.sleep(30) 

    def run(self):	
        expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                           "put_obj": {"ops": 1, "successful_ops": 1}}},
				  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
        expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
        expect_dict3 = {"entries_size": 1,
			"user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
        
        self.prepare()
        result1 = result2 = result3 = False
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)

	if result1 == result2 == result3 == True:
            print "testcase1                          %s" % (ok_display("OK"))
	else:
	    print "testcase1                          %s" % (fail_display("FAIL"))
	
	self.clean()

    def clean(self):
        exec_command('s3cmd -c user1.s3cfg rb s3://test1 --recursive')
        exec_command('s3cmd -c subuser2.s3cfg rb s3://test2')
	time.sleep(30)
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin usage trim --uid=user1')
        exec_command('./bin/radosgw-admin user rm --uid=user1 --purge-data --purge-keys')
        os.chdir(py_dir)

class TestCase2(object):
    def prepare(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin user create --uid=user1 --access-key=user1 --secret-key=user1 --display-name="user1"')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser1 --access=full --access-key=subuser1 --secret-key=subuser1')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser2 --access=full --access-key=subuser2 --secret-key=subuser2')
        os.chdir(py_dir) 

    def op1(self):
	exec_command('s3cmd -c subuser1.s3cfg mb s3://test1')
        time.sleep(30)
    
    def op2(self):
	exec_command('s3cmd -c subuser2.s3cfg put user1.s3cfg s3://test1')
        time.sleep(30)
   
    def op3(self):
        exec_command('s3cmd -c user1.s3cfg put subuser1.s3cfg s3://test1')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
        self.prepare()
	self.op1()
        expect_dict1 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict1)
        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict2)
        os.chdir(py_dir)
	if result1 == result2 == True:
	    self.op2()
	    expect_dict3 = {"entries_size": 1,
			    "user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                               "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
	    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
            os.chdir(py_dir)
	    if result1 == result2 ==result3 == True:
                self.op3()
                expect_dict6 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                                   "put_obj": {"ops": 2, "successful_ops": 2}}}}}
                expect_dict7 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict8 = {"entries_size": 1,
			        "user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict6)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict7)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict8)
                os.chdir(py_dir)
                if result1 == result2 ==result3 == True:
                    print "testcase2                          %s" % (ok_display("OK"))
		else:
		    print "testcase2                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase2                          %s" % (fail_display("FAIL"))
        else:
	    print "testcase2                          %s" % (fail_display("FAIL"))

class TestCase3(object):
    def op1(self):
	exec_command('s3cmd -c user1.s3cfg get s3://test1/user1.s3cfg 3-1.txt')
        exec_command('s3cmd -c user1.s3cfg get s3://test1/subuser1.s3cfg 3-2.txt')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg get s3://test1/user1.s3cfg 3-3.txt')
	exec_command('s3cmd -c subuser1.s3cfg get s3://test1/subuser1.s3cfg 3-4.txt')
	time.sleep(30)

    def op3(self):
        exec_command('s3cmd -c subuser2.s3cfg get s3://test1/user1.s3cfg 3-5.txt')
	exec_command('s3cmd -c subuser2.s3cfg get s3://test1/subuser1.s3cfg 3-6.txt')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                           "put_obj": {"ops": 2, "successful_ops": 2},
							   "get_obj": {"ops": 2, "successful_ops": 2}}}}}
	expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
	result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)
	if result1 == result2 == result3 == True:
            self.op2()	
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                               "put_obj": {"ops": 2, "successful_ops": 2},
							       "get_obj": {"ops": 4, "successful_ops": 4}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                                        "get_obj": {"ops": 2, "successful_ops": 2}}}}}
	    expect_dict6 = {"entries_size": 1,
			    "user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict6)
            os.chdir(py_dir)
	    if result1 == result2 ==result3 == True:
                self.op3()
                expect_dict7 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                                   "put_obj": {"ops": 2, "successful_ops": 2},
							           "get_obj": {"ops": 6, "successful_ops": 6}}}}}
	        expect_dict8 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                                            "get_obj": {"ops": 2, "successful_ops": 2}}}}}
		expect_dict9 = {"entries_size": 1,
			        "user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
					                                    "get_obj": {"ops": 2, "successful_ops": 2}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict9)
                os.chdir(py_dir)
		if result1 == result2 ==result3 == True:
                    print "testcase3                          %s" % (ok_display("OK"))
		else:
		    print "testcase3                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase3                          %s" % (fail_display("FAIL"))
	else:
	    print "testcase3                          %s" % (fail_display("FAIL"))

class TestCase4(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg del s3://test1/subuser1.s3cfg')
	time.sleep(30)

    def op2(self):
	exec_command('s3cmd -c subuser2.s3cfg del s3://test1/user1.s3cfg')
        time.sleep(30)

    def op3(self):
        exec_command('s3cmd -c user1.s3cfg rb s3://test1')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
	self.op1()
        expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                           "put_obj": {"ops": 2, "successful_ops": 2},
							   "get_obj": {"ops": 6, "successful_ops": 6},
							   "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
        expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                                    "get_obj": {"ops": 2, "successful_ops": 2}}}}}
        expect_dict3 = {"entries_size": 1,
			"user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
					                            "get_obj": {"ops": 2, "successful_ops": 2}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
	result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)
	if result1 == result2 == result3 == True:
	    self.op2()
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                               "put_obj": {"ops": 2, "successful_ops": 2},
							       "get_obj": {"ops": 6, "successful_ops": 6},
							       "delete_obj": {"ops": 2, "successful_ops": 2}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                                        "get_obj": {"ops": 2, "successful_ops": 2}}}}}
	    expect_dict6 = {"entries_size": 1,
			    "user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
					                                "get_obj": {"ops": 2, "successful_ops": 2},
									"delete_obj": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict6)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == True:
                self.op3()
		expect_dict7 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
				                                   "put_obj": {"ops": 2, "successful_ops": 2},
							           "get_obj": {"ops": 6, "successful_ops": 6},
							           "delete_obj": {"ops": 2, "successful_ops": 2},
								   "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict8 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                                            "get_obj": {"ops": 2, "successful_ops": 2}}}}}
		expect_dict9 = {"entries_size": 1,
			        "user1:subuser2": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
					                                    "get_obj": {"ops": 2, "successful_ops": 2},
									    "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict9)
                os.chdir(py_dir)
		if result1 == result2 ==result3 == True:
                    print "testcase4                          %s" % (ok_display("OK"))
		else:
		    print "testcase4                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase4                          %s" % (fail_display("FAIL"))
	else:
	    print "testcase4                          %s" % (fail_display("FAIL"))

	self.clean()

    def clean(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin usage trim --uid=user1')
        exec_command('./bin/radosgw-admin user rm --uid=user1 --purge-data --purge-keys')
        os.chdir(py_dir)
	exec_command('rm 3*.txt')

class TestCase5(object):
    def prepare(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin user create --uid=user1 --access-key=user1 --secret-key=user1 --display-name="user1"')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser1 --access=full --access-key=subuser1 --secret-key=subuser1')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser2 --access=full --access-key=subuser2 --secret-key=subuser2')
        os.chdir(py_dir)

    def op1(self):
	exec_command('s3cmd -c subuser1.s3cfg mb s3://test1')
	time.sleep(30)

    def op2(self):
	exec_command('s3cmd -c subuser2.s3cfg mb s3://test2')
	time.sleep(30)

    def op3(self):
        exec_command('s3cmd -c subuser1.s3cfg put user1.s3cfg s3://test2')
	time.sleep(30)

    def op4(self):
        exec_command('s3cmd -c user1.s3cfg mb s3://test3')
	exec_command('s3cmd -c user1.s3cfg put subuser1.s3cfg s3://test3')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
	self.prepare()
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 0}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)
	if result1 == result2 == result3 == True:
            self.op2()
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
                                      "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
			    "user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
            os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict6)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == True:
                self.op3()	
		expect_dict7 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			                  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                   "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict8 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
				                   "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict9 = {"entries_size": 1,
			        "user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
                result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict9)
                os.chdir(py_dir)
		if result1 == result2 == result3 == True:
		    self.op4()
		    expect_dict10 = {"entries_size": 1,
			             "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                        "put_obj": {"ops": 1, "successful_ops": 1}}},
					       "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                        "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	            expect_dict11 = {"entries_size": 1,
			             "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
				                        "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict12 = {"entries_size": 1,
			             "user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
                    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict10)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict11)
                    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict12)
                    os.chdir(py_dir)
		    if result1 == result2 == result3 == True:
	                print "testcase5                          %s" % (ok_display("OK"))
		    else:
                        print "testcase5                          %s" % (fail_display("FAIL"))
		else:
		    print "testcase5                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase5                          %s" % (fail_display("FAIL"))
	else:
	    print "testcase5                          %s" % (fail_display("FAIL"))

class TestCase6(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg get s3://test3/subuser1.s3cfg 6-1.txt')
	time.sleep(30)

    def op2(self):
	exec_command('s3cmd -c subuser1.s3cfg get s3://test2/user1.s3cfg 6-2.txt')
	exec_command('s3cmd -c subuser1.s3cfg get s3://test3/subuser1.s3cfg 6-3.txt')
	time.sleep(30)

    def op3(self):
	exec_command('s3cmd -c subuser2.s3cfg get s3://test2/user1.s3cfg 6-4.txt')
        exec_command('s3cmd -c subuser2.s3cfg get s3://test3/subuser1.s3cfg 6-5.txt')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						           "put_obj": {"ops": 1, "successful_ops": 1}}},
			          "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
				           "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}

        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)
	if result1 == result2 == result3 == True:
            self.op2()
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						               "put_obj": {"ops": 1, "successful_ops": 1},
						 	       "get_obj": {"ops": 1, "successful_ops": 1}}}, 
			              "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 2, "successful_ops": 2}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
				               "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
						                        "get_obj": {"ops": 1, "successful_ops": 1}}},
					       "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
			    "user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict6)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == True:
                self.op3()
		expect_dict7 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			                  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                   "put_obj": {"ops": 1, "successful_ops": 1},
							           "get_obj": {"ops": 2, "successful_ops": 2}}}, 
			                  "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                   "put_obj": {"ops": 1, "successful_ops": 1},
							           "get_obj": {"ops": 3, "successful_ops": 3}}}}}
		expect_dict8 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
				                   "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
						                            "get_obj": {"ops": 1, "successful_ops": 1}}},
					           "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict9 = {"entries_size": 1,
			        "user1:subuser2":  {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                    "get_obj": {"ops": 1, "successful_ops": 1}}},
				                    "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1}}}}}
		os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
                result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict9)
                os.chdir(py_dir)
		if result1 == result2 == result3 == True:
		    print "testcase6                          %s" % (ok_display("OK"))
		else:
		    print "testcase6                          %s" % (fail_display("FAIL"))
	    else:
                print "testcase6                          %s" % (fail_display("FAIL"))
	else:
	   print "testcase6                          %s" % (fail_display("FAIL"))

class TestCase7(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg ls s3://test1')
        exec_command('s3cmd -c user1.s3cfg ls s3://test2')
        exec_command('s3cmd -c user1.s3cfg ls s3://test3')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg ls s3://test1')
        exec_command('s3cmd -c subuser1.s3cfg ls s3://test2')
        exec_command('s3cmd -c subuser1.s3cfg ls s3://test3')
	time.sleep(30)

    def op3(self):
        exec_command('s3cmd -c subuser2.s3cfg ls s3://test1')
        exec_command('s3cmd -c subuser2.s3cfg ls s3://test2')
        exec_command('s3cmd -c subuser2.s3cfg ls s3://test3')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
        self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                           "list_bucket": {"ops": 1, "successful_ops": 1}}},
			          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 2, "successful_ops": 2},
							   "list_bucket": {"ops": 1, "successful_ops": 1}}}, 
			          "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 3, "successful_ops": 3},
							   "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
				           "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
						                    "get_obj": {"ops": 1, "successful_ops": 1}}},
					   "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                            "get_obj": {"ops": 1, "successful_ops": 1}}},
				           "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)
	if result1 == result2 == result3 == True:
            self.op2()
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                               "list_bucket": {"ops": 2, "successful_ops": 2}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 2, "successful_ops": 2},
							       "list_bucket": {"ops": 2, "successful_ops": 2}}}, 
			              "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 3, "successful_ops": 3},
							       "list_bucket": {"ops": 2, "successful_ops": 2}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
				                                        "list_bucket": {"ops": 1, "successful_ops": 1}}},
				               "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
						                        "get_obj": {"ops": 1, "successful_ops": 1},
									"list_bucket": {"ops": 1, "successful_ops": 1}}},
					       "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
						                        "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
			    "user1:subuser2": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                "get_obj": {"ops": 1, "successful_ops": 1}}},
				               "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1}}}}}
            os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict6)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == True:
	        self.op3()
		expect_dict7 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                   "list_bucket": {"ops": 3, "successful_ops": 3}}},
			                  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    			                   "put_obj": {"ops": 1, "successful_ops": 1},
			    				           "get_obj": {"ops": 2, "successful_ops": 2},
			    				           "list_bucket": {"ops": 3, "successful_ops": 3}}}, 
			                  "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    			                   "put_obj": {"ops": 1, "successful_ops": 1},
			    				           "get_obj": {"ops": 3, "successful_ops": 3},
			    				           "list_bucket": {"ops": 3, "successful_ops": 3}}}}}
		expect_dict8 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                            "list_bucket": {"ops": 1, "successful_ops": 1}}},
			    	                   "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
			    	    		                            "get_obj": {"ops": 1, "successful_ops": 1},
			    	    					    "list_bucket": {"ops": 1, "successful_ops": 1}}},
			    	    	           "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                            "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict9 = {"entries_size": 1,
			        "user1:subuser2": {"test1": {"categories": {"list_bucket": {"ops": 1, "successful_ops": 1}}},
				                   "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                    "get_obj": {"ops": 1, "successful_ops": 1},
									    "list_bucket": {"ops": 1, "successful_ops": 1}}},
				                   "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
							                    "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
                result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict9)
                os.chdir(py_dir)
		if result1 == result2 == result3 == True:
                    print "testcase7                          %s" % (ok_display("OK"))
		else:
		    print "testcase7                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase7                          %s" % (fail_display("FAIL"))
	else:
	    print "testcase7                          %s" % (fail_display("FAIL"))

class TestCase8(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg del s3://test3/subuser1.s3cfg')
	time.sleep(30)

    def op2(self):
	exec_command('s3cmd -c subuser1.s3cfg del s3://test2/user1.s3cfg')
	time.sleep(30)

    def op3(self):
	exec_command('s3cmd -c subuser2.s3cfg rb s3://test2')
	time.sleep(30)

    def op4(self):
        exec_command('s3cmd -c subuser1.s3cfg rb s3://test1')
        time.sleep(30)

    def op5(self):
	exec_command('s3cmd -c user1.s3cfg rb s3://test3')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = False
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                           "list_bucket": {"ops": 3, "successful_ops": 3}}},
			          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                   "put_obj": {"ops": 1, "successful_ops": 1},
			    			           "get_obj": {"ops": 2, "successful_ops": 2},
			   			           "list_bucket": {"ops": 3, "successful_ops": 3}}}, 
			          "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                   "put_obj": {"ops": 1, "successful_ops": 1},
			    			           "get_obj": {"ops": 3, "successful_ops": 3},
			    			           "list_bucket": {"ops": 3, "successful_ops": 3},
							   "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
        expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			                                            "list_bucket": {"ops": 1, "successful_ops": 1}}},
			    	           "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
			    	    		                    "get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                    "list_bucket": {"ops": 1, "successful_ops": 1}}},
			    	    	   "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                    "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user1:subuser2": {"test1": {"categories": {"list_bucket": {"ops": 1, "successful_ops": 1}}},
				           "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                            "get_obj": {"ops": 1, "successful_ops": 1},
							            "list_bucket": {"ops": 1, "successful_ops": 1}}},
				           "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
					                            "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict3)
        os.chdir(py_dir)
	if result1 == result2 == result3 == True:
            self.op2()	
	    expect_dict4 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                               "list_bucket": {"ops": 3, "successful_ops": 3}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                       "put_obj": {"ops": 1, "successful_ops": 1},
			    		        	       "get_obj": {"ops": 2, "successful_ops": 2},
			   			               "list_bucket": {"ops": 3, "successful_ops": 3},
							       "delete_obj": {"ops": 1, "successful_ops": 1}}},
			              "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                       "put_obj": {"ops": 1, "successful_ops": 1},
			    			               "get_obj": {"ops": 3, "successful_ops": 3},
			    			               "list_bucket": {"ops": 3, "successful_ops": 3},
							       "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict5 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			                                                "list_bucket": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
			    	    	    	                        "get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                        "list_bucket": {"ops": 1, "successful_ops": 1},
									"delete_obj": {"ops": 1, "successful_ops": 1}}},
			    	    	       "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                        "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
			    "user1:subuser2": {"test1": {"categories": {"list_bucket": {"ops": 1, "successful_ops": 1}}},
				               "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                "get_obj": {"ops": 1, "successful_ops": 1},
						      	                "list_bucket": {"ops": 1, "successful_ops": 1}}},
				               "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
					                                "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict4)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict5)
            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict6)
            os.chdir(py_dir)    
	    if result1 == result2 == result3 == True:
                self.op3()
	        expect_dict7 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                   "list_bucket": {"ops": 3, "successful_ops": 3}}},
			                  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                           "put_obj": {"ops": 1, "successful_ops": 1},
			    		           	           "get_obj": {"ops": 2, "successful_ops": 2},
			   			                   "list_bucket": {"ops": 3, "successful_ops": 3},
							           "delete_obj": {"ops": 1, "successful_ops": 1},
								   "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                  "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                           "put_obj": {"ops": 1, "successful_ops": 1},
			    			                   "get_obj": {"ops": 3, "successful_ops": 3},
			    			                   "list_bucket": {"ops": 3, "successful_ops": 3},
							           "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict8 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			                                                    "list_bucket": {"ops": 1, "successful_ops": 1}}},
			                           "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
			    	    	    	                            "get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                            "list_bucket": {"ops": 1, "successful_ops": 1},
								       	    "delete_obj": {"ops": 1, "successful_ops": 1}}},
			    	    	           "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                            "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict9 = {"entries_size": 1,
			        "user1:subuser2": {"test1": {"categories": {"list_bucket": {"ops": 1, "successful_ops": 1}}},
				                   "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                    "get_obj": {"ops": 1, "successful_ops": 1},
						       	                    "list_bucket": {"ops": 1, "successful_ops": 1},
									    "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				                   "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
					                                    "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
                result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict9)
                os.chdir(py_dir)
		if result1 == result2 == result3 == True:
                    self.op4()
		    expect_dict10 = {"entries_size": 1,
			             "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                       "list_bucket": {"ops": 3, "successful_ops": 3},
								       "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                               "put_obj": {"ops": 1, "successful_ops": 1},
			    		               	               "get_obj": {"ops": 2, "successful_ops": 2},
			   			                       "list_bucket": {"ops": 3, "successful_ops": 3},
						    	               "delete_obj": {"ops": 1, "successful_ops": 1},
						    		       "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                       "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                               "put_obj": {"ops": 1, "successful_ops": 1},
			    			                       "get_obj": {"ops": 3, "successful_ops": 3},
			    			                       "list_bucket": {"ops": 3, "successful_ops": 3},
							               "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict11 = {"entries_size": 1,
			             "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			                                                         "list_bucket": {"ops": 1, "successful_ops": 1},
										 "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                                "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
			    	    	    	                                 "get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                                 "list_bucket": {"ops": 1, "successful_ops": 1},
								       	         "delete_obj": {"ops": 1, "successful_ops": 1}}},
			    	    	                "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                                 "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict12 = {"entries_size": 1,
			             "user1:subuser2": {"test1": {"categories": {"list_bucket": {"ops": 1, "successful_ops": 1}}},
				                        "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                         "get_obj": {"ops": 1, "successful_ops": 1},
						       	                         "list_bucket": {"ops": 1, "successful_ops": 1},
										 "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				                        "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
					                                         "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict10)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict11)
                    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict12)
                    os.chdir(py_dir)
		    if result1 == result2 == result3 == True:
		        self.op5()
			expect_dict13 = {"entries_size": 1,
			                 "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                            "list_bucket": {"ops": 3, "successful_ops": 3},
								            "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                           "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                                    "put_obj": {"ops": 1, "successful_ops": 1},
			    		               	                    "get_obj": {"ops": 2, "successful_ops": 2},
			   			                            "list_bucket": {"ops": 3, "successful_ops": 3},
						    	                    "delete_obj": {"ops": 1, "successful_ops": 1},
						    		            "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                           "test3": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                                    "put_obj": {"ops": 1, "successful_ops": 1},
			    			                            "get_obj": {"ops": 3, "successful_ops": 3},
			    			                            "list_bucket": {"ops": 3, "successful_ops": 3},
							                    "delete_obj": {"ops": 1, "successful_ops": 1},
									    "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
                        expect_dict14 = {"entries_size": 1,
			                 "user1:subuser1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			                                                             "list_bucket": {"ops": 1, "successful_ops": 1},
								  		     "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                                    "test2": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
			    	    	    	                                     "get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                                     "list_bucket": {"ops": 1, "successful_ops": 1},
								       	             "delete_obj": {"ops": 1, "successful_ops": 1}}},
			    	    	                    "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
			    	    		                                     "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
			expect_dict15 = {"entries_size": 1,
			                 "user1:subuser2": {"test1": {"categories": {"list_bucket": {"ops": 1, "successful_ops": 1}}},
				                            "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                             "get_obj": {"ops": 1, "successful_ops": 1},
						       	                             "list_bucket": {"ops": 1, "successful_ops": 1},
										     "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				                            "test3": {"categories": {"get_obj": {"ops": 1, "successful_ops": 1},
					                                             "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
			os.chdir(ceph_path)
                        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict13)
	                result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict14)
                        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser2', expect_dict15)
                        os.chdir(py_dir)
		        if result1 == result2 == result3 == True:
                            print "testcase8                          %s" % (ok_display("OK"))
			else:
			    print "testcase8                          %s" % (fail_display("FAIL"))
		    else:
		        print "testcase8                          %s" % (fail_display("FAIL"))
		else:
		    print "testcase8                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase8                          %s" % (fail_display("FAIL"))
	else:
	    print "testcase8                          %s" % (fail_display("FAIL"))

	self.clean()
	
    def clean(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin usage trim --uid=user1')
        exec_command('./bin/radosgw-admin user rm --uid=user1 --purge-data --purge-keys')
        os.chdir(py_dir)
	exec_command('rm 6*.txt')

class TestCase9(object):
    def prepare(self):
	os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin user create --uid=user1 --access-key=user1 --secret-key=user1 --display-name="user1"')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser1 --access=full --access-key=subuser1 --secret-key=subuser1')
        os.chdir(py_dir)

    def op1(self):
        exec_command('s3cmd -c user1.s3cfg mb s3://test1')
	time.sleep(30)

    def op2(self):
	exec_command('s3cmd -c subuser1.s3cfg mb s3://test2')
	time.sleep(30)

    def op3(self):
        exec_command('s3cmd -c user1.s3cfg put user1.s3cfg s3://test2')
	time.sleep(30)

    def op4(self):
        exec_command('s3cmd -c subuser1.s3cfg put subuser1.s3cfg s3://test1')
	time.sleep(30)

    def op5(self):
        exec_command('s3cmd -c subuser1.s3cfg put subuser2.s3cfg s3://test2')
	time.sleep(30)

    def run(self):
        result1 = result2 = False
	self.prepare()
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
        expect_dict2 = {"entries_size": 0}
	os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        os.chdir(py_dir)
	if result1 == result2 == True:
            self.op2()	
	    expect_dict3 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict4 = {"entries_size": 1,
			    "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict3)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict4)
            os.chdir(py_dir)    
	    if result1 == result2 == True:
                self.op3()
	        expect_dict5 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}},
			                  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                           "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict6 = {"entries_size": 1,
			        "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}}	
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict5)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict6)
                os.chdir(py_dir)
		if result1 == result2 == True:
                    self.op4()
		    expect_dict7 = {"entries_size": 1,
			             "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
					                                "put_obj": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                               "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict8 = {"entries_size": 1,
			             "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}},
			                                "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}}}}} 
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
                    os.chdir(py_dir)
		    if result1 == result2 == True:
		        self.op5()
			expect_dict9 = {"entries_size": 1,
			                 "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
								            "put_obj": {"ops": 1, "successful_ops": 1}}},
			                           "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                                    "put_obj": {"ops": 2, "successful_ops": 2}}}}}
                        expect_dict10 = {"entries_size": 1,
			                 "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}},
			                                    "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	    	    	                                     "put_obj": {"ops": 1, "successful_ops": 1}}}}}	
			os.chdir(ceph_path)
                        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict9)
	                result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict10)
                        os.chdir(py_dir)
		        if result1 == result2 == True:
                            print "testcase9                          %s" % (ok_display("OK"))
			else:
			    print "testcase9                          %s" % (fail_display("FAIL"))
		    else:
		        print "testcase9                          %s" % (fail_display("FAIL"))
		else:
		    print "testcase9                          %s" % (fail_display("FAIL"))
	    else:
	        print "testcase9                          %s" % (fail_display("FAIL"))
	else:
	    print "testcase9                          %s" % (fail_display("FAIL"))

class TestCase10(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg get s3://test2/subuser2.s3cfg 10-1.txt')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg get s3://test2/user1.s3cfg 10-2.txt')
	exec_command('s3cmd -c subuser1.s3cfg get s3://test1/subuser1.s3cfg 10-3.txt')
	exec_command('s3cmd -c subuser1.s3cfg get s3://test2/subuser2.s3cfg 10-4.txt')
	time.sleep(30)

    def run(self):
        rsult1 = result2 = True
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1}}},
			          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                   "put_obj": {"ops": 2, "successful_ops": 2},
							   "get_obj": {"ops": 1, "successful_ops": 1}}}}}
        expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1}}},
			                   "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                    "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        os.chdir(py_dir)
	if result1 == result2 == True:
	    self.op2()
	    expect_dict3 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                       "put_obj": {"ops": 2, "successful_ops": 2},
						    	       "get_obj": {"ops": 3, "successful_ops": 3}}}}}
	    expect_dict4 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                        "get_obj": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                        "put_obj": {"ops": 1, "successful_ops": 1},
									"get_obj": {"ops": 2, "successful_ops": 2}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict3)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict4)
            os.chdir(py_dir)
	    if result1 == result2 == True:
                print "testcase10                         %s" % (ok_display("OK"))
	    else:
	        print "testcase10                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase10                         %s" % (fail_display("FAIL"))
	    
class TestCase11(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg ls s3://test1')
	exec_command('s3cmd -c user1.s3cfg ls s3://test2')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg ls s3://test1')
        exec_command('s3cmd -c subuser1.s3cfg ls s3://test2')
	time.sleep(30)

    def run(self):
        rsult1 = result2 = True
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1},
							   "list_bucket": {"ops": 1, "successful_ops": 1}}},
			          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                   "put_obj": {"ops": 2, "successful_ops": 2},
						    	   "get_obj": {"ops": 3, "successful_ops": 3},
							   "list_bucket": {"ops": 1, "successful_ops": 1}}}}} 
        expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                    "get_obj": {"ops": 1, "successful_ops": 1}}},
			                   "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                    "put_obj": {"ops": 1, "successful_ops": 1},
							  	    "get_obj": {"ops": 2, "successful_ops": 2}}}}}	
	os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        os.chdir(py_dir)
	if result1 == result2 == True:
	    self.op2()
	    expect_dict3 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1},
							       "list_bucket": {"ops": 2, "successful_ops": 2}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                       "put_obj": {"ops": 2, "successful_ops": 2},
						    	       "get_obj": {"ops": 3, "successful_ops": 3},
							       "list_bucket": {"ops": 2, "successful_ops": 2}}}}}
	    expect_dict4 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                        "get_obj": {"ops": 1, "successful_ops": 1},
									"list_bucket": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                        "put_obj": {"ops": 1, "successful_ops": 1},
									"get_obj": {"ops": 2, "successful_ops": 2},
									"list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict3)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict4)
            os.chdir(py_dir)
	    if result1 == result2 == True:
                print "testcase11                         %s" % (ok_display("OK"))
	    else:
	        print "testcase11                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase11                         %s" % (fail_display("FAIL"))

class TestCase12(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg del s3://test2/user1.s3cfg')
	time.sleep(30)

    def op2(self):
	exec_command('s3cmd -c subuser1.s3cfg del s3://test1/subuser1.s3cfg')
	time.sleep(30)

    def op3(self):
	exec_command('s3cmd -c user1.s3cfg rb s3://test1')
	time.sleep(30)

    def op4(self):
	exec_command('s3cmd -c subuser1.s3cfg del s3://test2/subuser2.s3cfg')
	time.sleep(30)

    def op5(self):
	exec_command('s3cmd -c subuser1.s3cfg rb s3://test2')
	time.sleep(30)

    def clean(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin usage trim --uid=user1')
        exec_command('./bin/radosgw-admin user rm --uid=user1 --purge-data --purge-keys')
        os.chdir(py_dir)
	exec_command('rm 10*.txt')

    def run(self):
        rsult1 = result2 = True
	self.op1()
	expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1},
							   "list_bucket": {"ops": 2, "successful_ops": 2}}},
			          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                   "put_obj": {"ops": 2, "successful_ops": 2},
						    	   "get_obj": {"ops": 3, "successful_ops": 3},
							   "list_bucket": {"ops": 2, "successful_ops": 2},
							   "delete_obj": {"ops": 1, "successful_ops": 1}}}}}	
        expect_dict2 = {"entries_size": 1,
			"user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                    "get_obj": {"ops": 1, "successful_ops": 1},
						                    "list_bucket": {"ops": 1, "successful_ops": 1}}},
			                   "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                    "put_obj": {"ops": 1, "successful_ops": 1},
						                    "get_obj": {"ops": 2, "successful_ops": 2},
								    "list_bucket": {"ops": 1, "successful_ops": 1}}}}}	
	os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
        os.chdir(py_dir)
	if result1 == result2 == True:
	    self.op2()
	    expect_dict3 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1},
							       "list_bucket": {"ops": 2, "successful_ops": 2},
							       "delete_obj": {"ops": 1, "successful_ops": 1}}},
			              "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                       "put_obj": {"ops": 2, "successful_ops": 2},
						    	       "get_obj": {"ops": 3, "successful_ops": 3},
							       "list_bucket": {"ops": 2, "successful_ops": 2},
							       "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict4 = {"entries_size": 1,
			    "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                        "get_obj": {"ops": 1, "successful_ops": 1},
									"list_bucket": {"ops": 1, "successful_ops": 1},
									"delete_obj": {"ops": 1, "successful_ops": 1}}},
			                       "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                        "put_obj": {"ops": 1, "successful_ops": 1},
									"get_obj": {"ops": 2, "successful_ops": 2},
									"list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict3)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict4)
            os.chdir(py_dir)
	    if result1 == result2 == True:
		self.op3()
		expect_dict5 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                   "put_obj": {"ops": 1, "successful_ops": 1},
							           "get_obj": {"ops": 1, "successful_ops": 1},
							           "list_bucket": {"ops": 2, "successful_ops": 2},
							           "delete_obj": {"ops": 1, "successful_ops": 1},
								   "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                           "put_obj": {"ops": 2, "successful_ops": 2},
						       	           "get_obj": {"ops": 3, "successful_ops": 3},
							           "list_bucket": {"ops": 2, "successful_ops": 2},
							           "delete_obj": {"ops": 1, "successful_ops": 1}}}}}
                expect_dict6 = {"entries_size": 1,
			        "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                            "get_obj": {"ops": 1, "successful_ops": 1},
									    "list_bucket": {"ops": 1, "successful_ops": 1},
									    "delete_obj": {"ops": 1, "successful_ops": 1}}},
			                           "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                            "put_obj": {"ops": 1, "successful_ops": 1},
									    "get_obj": {"ops": 2, "successful_ops": 2},
									    "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict5)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict6)
                os.chdir(py_dir)
		if result1 == result2 == True:
	            self.op4()
		    expect_dict7 = {"entries_size": 1,
			            "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                       "put_obj": {"ops": 1, "successful_ops": 1},
							               "get_obj": {"ops": 1, "successful_ops": 1},
							               "list_bucket": {"ops": 2, "successful_ops": 2},
							               "delete_obj": {"ops": 1, "successful_ops": 1},
								       "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                      "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                               "put_obj": {"ops": 2, "successful_ops": 2},
						       	               "get_obj": {"ops": 3, "successful_ops": 3},
							               "list_bucket": {"ops": 2, "successful_ops": 2},
							               "delete_obj": {"ops": 2, "successful_ops": 2}}}}}
		    expect_dict8 = {"entries_size": 1,
			            "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                                "get_obj": {"ops": 1, "successful_ops": 1},
									        "list_bucket": {"ops": 1, "successful_ops": 1},
									        "delete_obj": {"ops": 1, "successful_ops": 1}}},
			                               "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                                "put_obj": {"ops": 1, "successful_ops": 1},
									        "get_obj": {"ops": 2, "successful_ops": 2},
									        "list_bucket": {"ops": 1, "successful_ops": 1},
										"delete_obj": {"ops": 1, "successful_ops": 1}}}}}
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict7)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict8)
                    os.chdir(py_dir) 
		    if result1 == result2 == True:
	                self.op5()
			expect_dict9 = {"entries_size": 1,
			                "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                           "put_obj": {"ops": 1, "successful_ops": 1},
							                   "get_obj": {"ops": 1, "successful_ops": 1},
							                   "list_bucket": {"ops": 2, "successful_ops": 2},
							                   "delete_obj": {"ops": 1, "successful_ops": 1},
								           "delete_bucket": {"ops": 1, "successful_ops": 1}}},
			                          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    		                                   "put_obj": {"ops": 2, "successful_ops": 2},
					    	         	           "get_obj": {"ops": 3, "successful_ops": 3},
							                   "list_bucket": {"ops": 2, "successful_ops": 2},
							                   "delete_obj": {"ops": 2, "successful_ops": 2},
									   "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
			expect_dict10 = {"entries_size": 1,
			                 "user1:subuser1": {"test1": {"categories": {"put_obj": {"ops": 1, "successful_ops": 1},
				                                                     "get_obj": {"ops": 1, "successful_ops": 1},
									             "list_bucket": {"ops": 1, "successful_ops": 1},
									             "delete_obj": {"ops": 1, "successful_ops": 1}}},
			                                    "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
			    	                                                     "put_obj": {"ops": 1, "successful_ops": 1},
									             "get_obj": {"ops": 2, "successful_ops": 2},
									             "list_bucket": {"ops": 1, "successful_ops": 1},
									     	     "delete_obj": {"ops": 1, "successful_ops": 1},
										     "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
                        os.chdir(ceph_path)
                        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict9)
	                result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict10)
                        os.chdir(py_dir)
			if result1 == result2 == True: 
                            print "testcase12                         %s" % (ok_display("OK"))
			else:
			    print "testcase12                         %s" % (fail_display("FAIL"))
		    else:
		        print "testcase12                         %s" % (fail_display("FAIL"))
		else:
		    print "testcase12                         %s" % (fail_display("FAIL"))
	    else:
	        print "testcase12                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase12                         %s" % (fail_display("FAIL"))

	self.clean()

class TestCase13(object):
    def prepare(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin user create --uid=user1 --access-key=user1 --secret-key=user1 --display-name="user1"')
        exec_command('./bin/radosgw-admin user create --uid=user2 --access-key=user2 --secret-key=user2 --display-name="user2"')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser1 --access=full --access-key=subuser1 --secret-key=subuser1')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user1 --subuser=subuser2 --access=full --access-key=subuser2 --secret-key=subuser2')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user2 --subuser=subu01 --access=full --access-key=subu01 --secret-key=subu01')
        exec_command('./bin/radosgw-admin subuser create --key-type=s3 --uid=user2 --subuser=subu02 --access=full --access-key=subu02 --secret-key=subu02')
        os.chdir(py_dir)

    def op1(self):
        exec_command('s3cmd -c user1.s3cfg mb s3://test1')
	exec_command('s3cmd -c user1.s3cfg put user1.s3cfg s3://test1')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c user2.s3cfg mb s3://test01')
	exec_command('s3cmd -c user2.s3cfg put user2.s3cfg s3://test01')
	time.sleep(30)

    def op3(self):
	exec_command('s3cmd -c subuser1.s3cfg mb s3://test2')
	exec_command('s3cmd -c subuser1.s3cfg put subuser1.s3cfg s3://test2')
	time.sleep(30)

    def op4(self):
        exec_command('s3cmd -c subu01.s3cfg mb s3://test02')
	exec_command('s3cmd -c subu01.s3cfg put subu01.s3cfg s3://test02')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = result4 = False
	self.prepare()
	self.op1()
        expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 0}
	expect_dict3 = {"entries_size": 0}
	expect_dict4 = {"entries_size": 0}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
	result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict3)
	result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict4)
        os.chdir(py_dir)
	if result1 == result2 == result3 == result4 == True:
            self.op2()	
	    expect_dict5 = expect_dict1
	    expect_dict6 = expect_dict2
	    expect_dict7 = {"entries_size": 1,
			    "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict8 = expect_dict4
            os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict5)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict6)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict7)
	    result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict8)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == result4 == True:
                self.op3()
		expect_dict9 = {"entries_size": 1,
			        "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                   "put_obj": {"ops": 1, "successful_ops": 1}}},
				          "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                   "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	        expect_dict10 = {"entries_size": 1,
				 "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                             "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict11 = expect_dict7
		expect_dict12 = expect_dict8
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict9)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict10)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict11)
	        result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict12)
                os.chdir(py_dir)
		if result1 == result2 == result3 == result4 == True:
                    self.op4()
                    expect_dict13 = expect_dict9
		    expect_dict14 = expect_dict10
		    expect_dict15 = {"entries_size": 1,
			             "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1}}},
				               "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict16 = {"entries_size": 1,
				     "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                                "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict13)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict14)
	            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict15)
	            result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict16)
                    os.chdir(py_dir)
		    if result1 == result2 == result3 == result4 == True:
                        print "testcase13                         %s" % (ok_display("OK"))
                    else:
                        print "testcase13                         %s" % (fail_display("FAIL"))
		else:
                    print "testcase13                         %s" % (fail_display("FAIL"))
            else:
                print "testcase13                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase13                         %s" % (fail_display("FAIL"))

class TestCase14(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg get s3://test1/user1.s3cfg 14-1.txt')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg get s3://test2/subuser1.s3cfg 14-2.txt')
	time.sleep(30)
 
    def op3(self):
        exec_command('s3cmd -c user2.s3cfg get s3://test01/user2.s3cfg 14-3.txt')
	time.sleep(30)

    def op4(self):
	exec_command('s3cmd -c subu01.s3cfg get s3://test02/subu01.s3cfg 14-4.txt')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = result4 = False
	self.op1()
        expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1}}},
				  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
	                "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                    "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						            "put_obj": {"ops": 1, "successful_ops": 1}}},
				  "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						            "put_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict4 = {"entries_size": 1,
		        "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1},
						                   "put_obj": {"ops": 1, "successful_ops": 1}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
	result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict3)
	result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict4)
        os.chdir(py_dir)
	if result1 == result2 == result3 == result4 == True:
            self.op2()	
	    expect_dict5 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1}}},
				      "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
	                    "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                        "put_obj": {"ops": 1, "successful_ops": 1},
									"get_obj": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict7 = expect_dict3
	    expect_dict8 = expect_dict4
            os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict5)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict6)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict7)
	    result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict8)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == result4 == True:
                self.op3()
		expect_dict9 = expect_dict5
	        expect_dict10 = expect_dict6
		expect_dict11 = {"entries_size": 1,
			         "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                     "put_obj": {"ops": 1, "successful_ops": 1},
								     "get_obj": {"ops": 1, "successful_ops": 1}}},
				           "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                     "put_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict12 = expect_dict8
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict9)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict10)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict11)
	        result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict12)
                os.chdir(py_dir)
		if result1 == result2 == result3 == result4 == True:
                    self.op4()
                    expect_dict13 = expect_dict9
		    expect_dict14 = expect_dict10
		    expect_dict15 = {"entries_size": 1,
			             "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1},
								         "get_obj": {"ops": 1, "successful_ops": 1}}},
				               "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1},
									 "get_obj": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict16 = {"entries_size": 1,
				     "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                                "put_obj": {"ops": 1, "successful_ops": 1},
										"get_obj": {"ops": 1, "successful_ops": 1}}}}}
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict13)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict14)
	            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict15)
	            result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict16)
                    os.chdir(py_dir)
		    if result1 == result2 == result3 == result4 == True:
                        print "testcase14                         %s" % (ok_display("OK"))
                    else:
                        print "testcase14                         %s" % (fail_display("FAIL"))
		else:
                    print "testcase14                         %s" % (fail_display("FAIL"))
            else:
                print "testcase14                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase14                         %s" % (fail_display("FAIL"))

class TestCase15(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg ls s3://test1')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg ls s3://test2')
	time.sleep(30)

    def op3(self):
        exec_command('s3cmd -c user2.s3cfg ls s3://test01')
	time.sleep(30)

    def op4(self):
	exec_command('s3cmd -c subu01.s3cfg ls s3://test02')
	time.sleep(30)

    def run(self):
        result1 = result2 = result3 = result4 = False
	self.op1()
        expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1},
							   "list_bucket": {"ops": 1, "successful_ops": 1}}},
				  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
	                "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                    "put_obj": {"ops": 1, "successful_ops": 1},
						                    "get_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						            "put_obj": {"ops": 1, "successful_ops": 1},
						            "get_obj": {"ops": 1, "successful_ops": 1}}},
				  "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						            "put_obj": {"ops": 1, "successful_ops": 1},
						            "get_obj": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict4 = {"entries_size": 1,
	                "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                   "put_obj": {"ops": 1, "successful_ops": 1},
							           "get_obj": {"ops": 1, "successful_ops": 1}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
	result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict3)
	result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict4)
        os.chdir(py_dir)
	if result1 == result2 == result3 == result4 == True:
            self.op2()	
	    expect_dict5 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1},
							       "list_bucket": {"ops": 1, "successful_ops": 1}}},
				      "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1},
							       "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
	                    "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                        "put_obj": {"ops": 1, "successful_ops": 1},
									"get_obj": {"ops": 1, "successful_ops": 1},
									"list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict7 = expect_dict3
	    expect_dict8 = expect_dict4
            os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict5)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict6)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict7)
	    result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict8)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == result4 == True:
                self.op3()
		expect_dict9 = expect_dict5
	        expect_dict10 = expect_dict6
		expect_dict11 = {"entries_size": 1,
			         "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                     "put_obj": {"ops": 1, "successful_ops": 1},
						                     "get_obj": {"ops": 1, "successful_ops": 1},
								     "list_bucket": {"ops": 1, "successful_ops": 1}}},
				           "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                     "put_obj": {"ops": 1, "successful_ops": 1},
						                     "get_obj": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict12 = expect_dict8
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict9)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict10)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict11)
	        result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict12)
                os.chdir(py_dir)
		if result1 == result2 == result3 == result4 == True:
                    self.op4()
                    expect_dict13 = expect_dict9
		    expect_dict14 = expect_dict10
		    expect_dict15 = {"entries_size": 1,
			             "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1},
								         "get_obj": {"ops": 1, "successful_ops": 1},
									 "list_bucket": {"ops": 1, "successful_ops": 1}}},
				               "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1},
									 "get_obj": {"ops": 1, "successful_ops": 1},
									 "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict16 = {"entries_size": 1,
				     "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                                "put_obj": {"ops": 1, "successful_ops": 1},
										"get_obj": {"ops": 1, "successful_ops": 1},
										"list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict13)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict14)
	            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict15)
	            result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict16)
                    os.chdir(py_dir)
		    if result1 == result2 == result3 == result4 == True:
                        print "testcase15                         %s" % (ok_display("OK"))
                    else:
                        print "testcase15                         %s" % (fail_display("FAIL"))
		else:
                    print "testcase15                         %s" % (fail_display("FAIL"))
            else:
                print "testcase15                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase15                         %s" % (fail_display("FAIL"))

class TestCase16(object):
    def op1(self):
        exec_command('s3cmd -c user1.s3cfg del s3://test1/user1.s3cfg')
	exec_command('s3cmd -c user1.s3cfg rb s3://test1')
	time.sleep(30)

    def op2(self):
        exec_command('s3cmd -c subuser1.s3cfg del s3://test2/subuser1.s3cfg')
	exec_command('s3cmd -c subuser1.s3cfg rb s3://test2')
	time.sleep(30)

    def op3(self):
	exec_command('s3cmd -c user2.s3cfg del s3://test01/user2.s3cfg')
	exec_command('s3cmd -c user2.s3cfg rb s3://test01')
	time.sleep(30)

    def op4(self):
        exec_command('s3cmd -c subu01.s3cfg del s3://test02/subu01.s3cfg')
	exec_command('s3cmd -c subu01.s3cfg rb s3://test02')
	time.sleep(30)

    def clean(self):
        os.chdir(ceph_path)
        exec_command('./bin/radosgw-admin usage trim --uid=user1')
        exec_command('./bin/radosgw-admin user rm --uid=user1 --purge-data --purge-keys')
        exec_command('./bin/radosgw-admin usage trim --uid=user2')
        exec_command('./bin/radosgw-admin user rm --uid=user2 --purge-data --purge-keys')
        os.chdir(py_dir)
	exec_command('rm 14*.txt')

    def run(self):
        result1 = result2 = result3 = result4 = False
	self.op1()
        expect_dict1 = {"entries_size": 1,
			"user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
					                   "get_obj": {"ops": 1, "successful_ops": 1},
						           "list_bucket": {"ops": 1, "successful_ops": 1},
							   "delete_obj": {"ops": 1, "successful_ops": 1},
							   "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				  "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						           "put_obj": {"ops": 1, "successful_ops": 1},
							   "get_obj": {"ops": 1, "successful_ops": 1},
							   "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict2 = {"entries_size": 1,
	                "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                    "put_obj": {"ops": 1, "successful_ops": 1},
						                    "get_obj": {"ops": 1, "successful_ops": 1},
								    "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict3 = {"entries_size": 1,
			"user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						            "put_obj": {"ops": 1, "successful_ops": 1},
						            "get_obj": {"ops": 1, "successful_ops": 1},
							    "list_bucket": {"ops": 1, "successful_ops": 1}}},
				  "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						            "put_obj": {"ops": 1, "successful_ops": 1},
						            "get_obj": {"ops": 1, "successful_ops": 1},
						            "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
	expect_dict4 = {"entries_size": 1,
	                "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                   "put_obj": {"ops": 1, "successful_ops": 1},
							           "get_obj": {"ops": 1, "successful_ops": 1},
								   "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
        os.chdir(ceph_path)
        result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict1)
	result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict2)
	result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict3)
	result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict4)
        os.chdir(py_dir)
	if result1 == result2 == result3 == result4 == True:
            self.op2()	
	    expect_dict5 = {"entries_size": 1,
			    "user1": {"test1": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
					                       "get_obj": {"ops": 1, "successful_ops": 1},
						               "list_bucket": {"ops": 1, "successful_ops": 1},
							       "delete_obj": {"ops": 1, "successful_ops": 1},
							       "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				      "test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						               "put_obj": {"ops": 1, "successful_ops": 1},
							       "get_obj": {"ops": 1, "successful_ops": 1},
							       "list_bucket": {"ops": 1, "successful_ops": 1},
							       "delete_obj": {"ops": 1, "successful_ops": 1},
							       "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict6 = {"entries_size": 1,
	                    "user1:subuser1": {"test2": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                        "put_obj": {"ops": 1, "successful_ops": 1},
									"get_obj": {"ops": 1, "successful_ops": 1},
									"list_bucket": {"ops": 1, "successful_ops": 1},
									"delete_obj": {"ops": 1, "successful_ops": 1},
									"delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
	    expect_dict7 = expect_dict3
	    expect_dict8 = expect_dict4
            os.chdir(ceph_path)
            result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict5)
	    result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict6)
	    result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict7)
	    result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict8)
            os.chdir(py_dir)
	    if result1 == result2 == result3 == result4 == True:
                self.op3()
		expect_dict9 = expect_dict5
	        expect_dict10 = expect_dict6
		expect_dict11 = {"entries_size": 1,
			         "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                     "put_obj": {"ops": 1, "successful_ops": 1},
						                     "get_obj": {"ops": 1, "successful_ops": 1},
							             "list_bucket": {"ops": 1, "successful_ops": 1},
								     "delete_obj": {"ops": 1, "successful_ops": 1},
								     "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				           "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                     "put_obj": {"ops": 1, "successful_ops": 1},
						                     "get_obj": {"ops": 1, "successful_ops": 1},
						                     "list_bucket": {"ops": 1, "successful_ops": 1}}}}}
		expect_dict12 = expect_dict8
                os.chdir(ceph_path)
                result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict9)
	        result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict10)
	        result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict11)
	        result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict12)
                os.chdir(py_dir)
		if result1 == result2 == result3 == result4 == True:
                    self.op4()
                    expect_dict13 = expect_dict9
		    expect_dict14 = expect_dict10
		    expect_dict15 = {"entries_size": 1,
			             "user2": {"test01": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1},
								         "get_obj": {"ops": 1, "successful_ops": 1},
									 "list_bucket": {"ops": 1, "successful_ops": 1},
									 "delete_obj": {"ops": 1, "successful_ops": 1},
								         "delete_bucket": {"ops": 1, "successful_ops": 1}}},
				               "test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                         "put_obj": {"ops": 1, "successful_ops": 1},
									 "get_obj": {"ops": 1, "successful_ops": 1},
									 "list_bucket": {"ops": 1, "successful_ops": 1},
									 "delete_obj": {"ops": 1, "successful_ops": 1},
								         "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
		    expect_dict16 = {"entries_size": 1,
				     "user2:subu01": {"test02": {"categories": {"create_bucket": {"ops": 1, "successful_ops": 1}, 
						                                "put_obj": {"ops": 1, "successful_ops": 1},
										"get_obj": {"ops": 1, "successful_ops": 1},
										"list_bucket": {"ops": 1, "successful_ops": 1},
										"delete_obj": {"ops": 1, "successful_ops": 1},
								                "delete_bucket": {"ops": 1, "successful_ops": 1}}}}}
		    os.chdir(ceph_path)
                    result1 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1', expect_dict13)
	            result2 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user1 --subuser=subuser1', expect_dict14)
	            result3 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2', expect_dict15)
	            result4 = verify_show_response_msg('./bin/radosgw-admin usage show --uid=user2 --subuser=subu01', expect_dict16)
                    os.chdir(py_dir)
		    if result1 == result2 == result3 == result4 == True:
                        print "testcase16                         %s" % (ok_display("OK"))
                    else:
                        print "testcase16                         %s" % (fail_display("FAIL"))
		else:
                    print "testcase16                         %s" % (fail_display("FAIL"))
            else:
                print "testcase16                         %s" % (fail_display("FAIL"))
	else:
	    print "testcase16                         %s" % (fail_display("FAIL"))

	self.clean()


if __name__ == '__main__': 
    test_case1 = TestCase1()
    test_case1.run()
    test_case2 = TestCase2()
    test_case2.run()
    test_case3 = TestCase3()
    test_case3.run()
    test_case4 = TestCase4()
    test_case4.run()
    test_case5 = TestCase5()
    test_case5.run()
    test_case6 = TestCase6()
    test_case6.run()
    test_case7 = TestCase7()
    test_case7.run()
    test_case8 = TestCase8()
    test_case8.run()
    test_case9 = TestCase9()
    test_case9.run()
    test_case10 = TestCase10()
    test_case10.run()
    test_case11 = TestCase11()
    test_case11.run()
    test_case12 = TestCase12()
    test_case12.run()
    test_case13 = TestCase13()
    test_case13.run()
    test_case14 = TestCase14()
    test_case14.run()
    test_case15 = TestCase15()
    test_case15.run()
    test_case16 = TestCase16()
    test_case16.run()
