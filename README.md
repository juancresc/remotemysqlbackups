# remotemysqlbackups
Make, transfer and restore remote mysql dumps via ssh


## How to use:

**Edit de databases config file as follow:**
```
[config]
deletemonths=2
localuser=root
localpass=localrootpassword

[backup-somedatabase]
sshhost=someIP
sshuser=someSSHUser
dbuser=somedbuser
dbname=somedbname
dbpass=somedbpass

[backup-anotherdatabase]
sshhost=anotherIP
sshuser=anotherSSHUser
dbuser=anotherdbuser
dbname=anotherdbname
dbpass=anotherdbpass
```

You can add as many backups as you want. 

**Main config:**

deletemonths: Specify how many months you want to keep the backups. After that time they will be deleted 
localuser: Root mysql user, will be used to restore the backup in the local machine
localpass: Local root mysql password

**Backup config:**

All backups must be backup-*
For now, you must have access to the remote server via ssh-copy-id.
db* are simply the remote database settings.


**Todo:**

1. deletemonths: disable and specify in days
2. Allow login to ssh via password
