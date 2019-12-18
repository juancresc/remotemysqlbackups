#!/usr/bin/env python
# -*- coding: utf-8 -*-
#apt python-dev
#pip pycrypto paramiko ecdsa configparser
import datetime
from dateutil.relativedelta import relativedelta
from time import gmtime, strftime
from paramiko import SSHClient
from scp import SCPClient
import configparser
import paramiko
import os
import argparse
import logging
import subprocess
#LOG_FILENAME = 'remote-backup-log.out'
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG,)

parser = argparse.ArgumentParser()#pylint: disable=invalid-name
parser.add_argument("-nr", "--norestore", help="Don't restore in local mysql", action='store_true')

args = parser.parse_args()#pylint: disable=invalid-name

curr_path = "/".join(os.path.abspath(__file__).split("/")[0:-1])
ssh = SSHClient()
ssh.load_system_host_keys()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print( " backup script started at: ", strftime("%Y-%m-%d %H%M%S", gmtime()))
config = configparser.ConfigParser()
config.read(curr_path + '/databases')

hosts = config.sections()

deletemonths = ""
localuser = ""
localpass = ""
for h in hosts:
	if h.startswith("config"):
		deletemonths = config[h]["deletemonths"]
		localuser = config[h]["localuser"]
		localpass = config[h]["localpass"]
	if not h.startswith("backup-"):
		continue
	#create remote backup command
	timestamp = strftime("%Y%m%d_%H%M%S", gmtime())
	filename = config[h]['dbname'] + "_" + timestamp + ".sql.gz"
	dumpcmd = "mysqldump -u " + config[h]['dbuser'] + " -p" + config[h]['dbpass'] + " " + config[h]['dbname'] +  " | gzip > " + filename

	#connects to remote host
	try:
		#ssh.connect(config[h]['sshhost'], username=config[h]['sshuser'], password=config[h]['sshpass'], timeout=10)
		print("connecting to ", config[h]['sshhost'])
		ssh.connect(config[h]['sshhost'], username=config[h]['sshuser'], timeout=10)
	except paramiko.AuthenticationException:
		print("login failed on ", config[h]['sshhost'])
		continue
  		
  	#executes mysqldump
	stdin, stdout, stderr = ssh.exec_command(dumpcmd)
	channel = stdout.channel
	print(filename, " dump started ")
	status = channel.recv_exit_status()
	print( filename, " dump finished ")

	#creates scp client
	scp = SCPClient(ssh.get_transport())

	#calculate local target directory
	target_dir = curr_path + "/backups/" + config[h]['dbname'] + "/" + strftime("%Y/%m", gmtime())
	
	local_db_path = target_dir + "/" + filename
	#create current directory
	if not os.path.exists(target_dir):
		os.makedirs(target_dir)

	print("downloading ", filename)
	scp.get(filename, local_db_path)
	print(filename, " downloaded ")

	removecmd = "rm %s " % (filename, )
	stdin, stdout, stderr = ssh.exec_command(removecmd)
	channel = stdout.channel
	print(filename, " remove started ")
	status = channel.recv_exit_status()
	print(filename, " remove finished ")
	if not args.norestore:
		import MySQLdb as db
		con = db.connect(user=localuser, passwd=localpass)
		cur = con.cursor()
		cur.execute('CREATE DATABASE IF NOT EXISTS %s' % config[h]['dbname'])
		print("database ", config[h]['dbname'], " created (if not existed) ")

		#optional via bash without python-mysql
		#create_db_cmd = "echo 'CREATE DATABASE IF NOT EXISTS %s' | mysql -u %s -p%s" % (config[h]['dbname'],localuser, localpass)
		#process = subprocess.Popen(create_db_cmd, shell=True, stdout=subprocess.PIPE)
		#print create_db_cmd
		#process.wait()
		#print "database ", config[h]['dbname'], " created (if not existed) "

		#import database to local server
		restore_cmd = "zcat %s | mysql -u %s -p%s %s " % (local_db_path, localuser, localpass, config[h]['dbname'])
		process = subprocess.Popen(restore_cmd, shell=True, stdout=subprocess.PIPE)
		process.wait()
		print(config[h]['dbname'], " restored ")
		#delete remote dump
		stdin, stdout, stderr = ssh.exec_command("rm " + filename)	
	scp.close()
	ssh.close()

#calculate minus $deletemonths month date
#today = datetime.date.today()
#first = today.replace(day=1)
#selected_month = first - relativedelta(months=int(deletemonths))
#delete_month = selected_month.strftime("%m")
#delete_year = selected_month.strftime("%Y")
#delete_dir = "backups/" + config[h]['dbname'] + "/" + str(delete_year) + "/" + str(delete_month)
#deletes old directory
#delete_cmd = "rm -Rf %s" % delete_dir
#process = subprocess.Popen(delete_cmd, shell=True, stdout=subprocess.PIPE)
#print delete_cmd
print("backup script finished at: ", strftime("%Y-%m-%d %H%M%S", gmtime()))