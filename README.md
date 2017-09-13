# VmBackup
XenServer Backup Script

## Overview
 - The VmBackup.py script is run from a XenServer host and utilizes the native `xe vm-export` and `xe vdi-export` commands to backup both Linux and Windows VMs. 
 - The vm-export or vdi-export is run after a respective vm-snapshot or vdi-snapshot occurs, which allows for the export to execute while the VM is up and running.
 - These backup command techniques were originally discovered from anonymous Internet sources, then modified and developed into this python code. The new vdi-export feature was developed from information found at http://wiki.xensource.com/wiki/Disk_import/export_APIs
 - During the backup of specified VMs, this script collects additional VM metadata using the XenServer XenAPI. This additional information can be useful during VM restore situations and is stored in each individual VM backup location.
 - Typically, VmBackup.py is implemented through scheduled crontab entries or can be run manually on a XenServer ssh session. It is important to keep in mind that the backup process does use critical dom0 resources, so running a backup during heavy workloads should be avoided (especially if used with ```compress``` option).
 - The SRs where one or more VDIs are located require sufficient free space to hold a complete snapshot of a VM. The temporary snapshots that are created during the backup process are deleted after the vm-export has completed.
 - If the config-file pool_db_backup=1 is specified, then the pool state backup occurs via the `xe pool-dump-database` command. 
 - Optionally, a completion status email can be sent by configuring VmBackup.py variables that are provided in the code, see the Quick Start Checklist section.

## Quick Start Checklist

1. VmBackup will require lots of file storage. Set up a storage server with an exported VM backup share. Frequently NFS is used for the storage server, with many installation and configuration sources available on the web. An optional SMB/CIFS method can be enabled through comments in the script.
2. For all of the XenServers in a given pool, mount the new share at your desired filesystem location (default script location is /mnt/VmBackup). 
3. Finish creating a share directory structure that meets your needs. Here are the VmBackup.py default subdirectories which can be changed:
   - /mnt/VmBackup/exports - this is for all VM backups
   - /mnt/VmBackup - this is for the VmBackup.py script, any config files, and the status.log summary file.
   - /mnt/VmBackup/logs - this is for redirecting your cronjob VmBackup.py output.
4. Download VmBackup.py, example.cfg, README.md to your execution location, such as /mnt/VmBackup
5. Inspect and customize certain options in the VmBackup.py code. Here are some of the changes you may want to configure:
 - Find text HARD CODED DEFAULTS - these values are in effect anytime you run VmBackup.py with a command line vm-selector. Many of these code defaults can also be overridden in the config-file.
 - Find text OPTIONAL - if you want an automatic email to be sent at end of VmBackup then follow the instructions for the label MAIL_ENABLE. 
6. Install the XenServer Software Development Kit from www.citrix.com/downloads - download the XenServer and copy file XenAPI.py into the same directory where VmBackup.py exists.
   - To verfy XenApi, execute VmBackup with a valid password and some simple vm-name.
   - Example: ./VmBackup.py password vm-name preview 
   - Note: if password has any special characters, then escape with back slash: ./VmBackup.py pass\$word vm-name
7. Follow some VmBackup usage examples in the next section and try some examples with your VMs. Initially use the `preview` option, followed by a non-preview execution to actually see the VM export process. If you have a test XenServer environment, then utilize this for test verification.
8. VM Recovery testing is an important part of the setup, see later section. Become familiar with the /mnt/VmBackup/exports/vm-name directory structure and file contents, also in later section. After backing up some VMs then restore them on a test system and verify VM functionality.
9. Plan your backup strategy, such as weekly, bi-monthly, monthly frequencies. How many copies of each backup do you want to keep? How long do your backup configurations take to execute and does this fit in with your XenServer processing priorities?
10. Execute your plan which typically involves setting up a XenServer crontab schedule, see later section.

## VmBackup.py Command Usage

#### Basic usage:

	./VmBackup.py
	
	Usage:
	./VmBackup.py  <password> <config-file|vm-selector> [preview] [other optional params]
	
	Also: VmBackup.py help    - for additional parameter usage
	  or: VmBackup.py config  - for config-file parameter usage
	  or: VmBackup.py example - for some simple example usage


#### Detail usage:

	./VmBackup.py help
  
	Usage-help:
	./VmBackup.py  <password|password-file> <config-file|vm-selector> [preview] [other optional params]

	required params:
  		<password|password-file> - xenserver password or obscured password stored in password-file
  		<config-file|vm-selector> - several options:
    		config-file - a common choice for production crontab execution
    		vm-selector - a single vm name or vm prefix wildcard that defaults to vm-export
    			note: with vm-selector then config defaults are set from VmBackup.py default constants
    		vm-export=vm-selector  - explicit vm-export
    		vdi-export=vm-selector - explicit vdi-export

	optional params:
  		[preview] - preview/validate VmBackup config parameters and XenServer password
  		[compress=True|False] - automatic compression of backup (only for vm-export function) (default: False)
  		[ignore_extra_keys=True|False] - some config files may have extra params (default: False)

	alternate form - create-password-file:
	./VmBackup.py  <password> create-password-file=filename

  		create-password-file=filename - create an obscured password file with the specified password
  		note: password filename is relative to current path or absolute path.


#### Some simple examples:

	./VmBackup.py example
	
	Usage-examples:

	# config file
	./VmBackup.py password weekend.cfg

	# single VM name, which is case sensitive
	./VmBackup.py password DEV-MYSQL

	# single VM name using vdi-export instead of vm-export
	./VmBackup.py password vdi-export=DEV-MYSQL

	# single VM name with spaces in name
	./VmBackup.py password "DEV MYSQL"

	# VM prefix wildcard - which may be more than one VM
	./VmBackup.py password DEV-MY.*

	# all VMs in pool
	./VmBackup.py password .*
	
	Alternate form - create-password-file:
	# create password file from command line password
	./VmBackup.py password create-password-file=/root/VmBackup.pass

	# use password file + config file
	./VmBackup.py /root/VmBackup.pass monthly.cfg

#### Preview Example #1 - VmBackup.py with vm-selector
 
 Preview is useful after config-file changes for production crontab backups that will run later.
 
```
./VmBackup.py password "Dev MYSQL" preview
2017-09-12-(23:51:59) - Running with default config
2017-09-12-(23:51:59) - VmBackup.py running with these settings:
2017-09-12-(23:51:59) -   backup_dir        = /mnt/VmBackup/EXPORTS
2017-09-12-(23:51:59) -   status_log        = /mnt/VmBackup/status.log
2017-09-12-(23:51:59) -   compress          = False
2017-09-12-(23:51:59) -   max_backups       = 4
2017-09-12-(23:51:59) -   vdi_export_format = raw
2017-09-12-(23:51:59) -   pool_db_backup    = 0
2017-09-12-(23:51:59) -   exclude (cnt)= 0
2017-09-12-(23:51:59) -   exclude:
2017-09-12-(23:51:59) -   vdi-export (cnt)= 0
2017-09-12-(23:51:59) -   vdi-export:
2017-09-12-(23:51:59) -   vm-export (cnt)= 1
2017-09-12-(23:51:59) -   vm-export: DEV MYSQL
2017-09-12-(23:51:59) - SUCCESS preview of parameters
```

#### Preview Example #2 - VmBackup.py with config-file

**Example with configuration errors present:**
```
cat weekend.cfg
# Weekend VMs - with VM name errors
max_backups=4
backup_dir=/mnt/VmBackup/EXPORTS
vdi-export=PROD-CentOS7.large-user-disks
vm-export=PROD.*
exclude=PROD-ubuntu12.1

./VmBackup.py password weekend.cfg preview

2017-09-12-(23:51:59) - ***WARNING - vm not found: exclude=PROD-ubuntu12.1
2017-09-12-(23:51:59) - ***WARNING - vm not found: vdi-export=PROD-CentOS7.large-user-disks
2017-09-12-(23:51:59) - VmBackup config loaded from: /mnt/VmBackup/weekly.cfg
2017-09-12-(23:51:59) - VmBackup.py running with these settings:
2017-09-12-(23:51:59) -   backup_dir        = /mnt/VmBackup/EXPORTS
2017-09-12-(23:51:59) -   status_log        = /mnt/VmBackup/status.log
2017-09-12-(23:51:59) -   compress          = False
2017-09-12-(23:51:59) -   max_backups       = 4
2017-09-12-(23:51:59) -   vdi_export_format = raw
2017-09-12-(23:51:59) -   pool_db_backup    = 0
2017-09-12-(23:51:59) -   exclude (cnt)= 0
2017-09-12-(23:51:59) -   exclude:
2017-09-12-(23:51:59) -   vdi-export (cnt)= 0
2017-09-12-(23:51:59) -   vdi-export:
2017-09-12-(23:51:59) -   vm-export (cnt)= 4
2017-09-12-(23:51:59) -   vm-export: PROD-CentOS7-large-user-disks, PROD-ubuntu12-1, PROD-ubuntu14, PROD-WinSvr
2017-09-12-(23:51:59) - SUCCESS preview of parameters  - WARNINGS found (see above)
```

**Example with configuration errors resolved:**

```
cat weekend.cfg
# Weekend VMs - with no errors
max_backups=4
backup_dir=/mnt/VmBackup/EXPORTS
vdi-export=PROD-CentOS7-large-user-disks
vm-export=PROD.*
exclude=PROD-ubuntu12-1

./VmBackup.py password weekend.cfg preview
2017-09-12-(23:51:59) - VmBackup config loaded from: /mnt/VmBackup/weekly.cfg
2017-09-12-(23:51:59) - VmBackup.py running with these settings:
2017-09-12-(23:51:59) -   backup_dir        = /mnt/VmBackup/EXPORTS
2017-09-12-(23:51:59) -   status_log        = /mnt/VmBackup/status.log
2017-09-12-(23:51:59) -   compress          = False
2017-09-12-(23:51:59) -   max_backups       = 4
2017-09-12-(23:51:59) -   vdi_export_format = raw
2017-09-12-(23:51:59) -   pool_db_backup    = 0
2017-09-12-(23:51:59) -   exclude (cnt)= 1
2017-09-12-(23:51:59) -   exclude: PROD-ubuntu12-1
2017-09-12-(23:51:59) -   vdi-export (cnt)= 1
2017-09-12-(23:51:59) -   vdi-export: PROD-CentOS7-large-user-disks
2017-09-12-(23:51:59) -   vm-export (cnt)= 2
2017-09-12-(23:51:59) -   vm-export: PROD-ubuntu14, PROD-WinSvr
2017-09-12-(23:51:59) - SUCCESS preview of parameters
```

### A few words about Python REGEX syntax

For the handling of wildcard VMs, VmBackup incorporates the native python regex library of regular expressions. **WARNING:** The syntax is slightly different from what is processed with the Linux family of grep commands. In python, a string followed by ```*``` causes the resulting regular expression to match zero or more repetitions of the preceding regular expression, as many repetitions as are possible. For example, ```ab*``` will match "a", "ab", or "a" followed by any number of "b" characters. Therefore, if you had PRD-a*, this will match PRD-a, PRD-aa, PRD-aaaSomething, as well as PRD- but _also_ PRD-Test, PRD-123 and anything else starting with PRD- since zero occurences of the "a" after the "-" are matched. To avoid this, PRD-a.* should be used, instead, indicating in this case PRD-a followed by any single character (".") zero or more("*") times.

Note that the current implementation uses the re.match function which by design is expected to be front-anchored. You can explicitly preface a search string with the "^" operator, if desired, but it is already implied and the results will be the same.

A VM name is considered to be a simple (non-wildcard) name, provided that it contains only combinations of any of the following: letters (upper as well as lower case), numerals 0 through 9, the space character, hyphens (dashes), and underscore characters. These will _not be handled using regex operations!_

Here are some examples of regex selections. Note that if a vdi-export definition is encoutered in the configuration file before a matching vm-export definition, the vdi-export will take precedence. Recall also that exclude definitions will apply before all vdi-export and vm-export rules.

	# exclude simple host names (non-wildcard instances)
	exclude=DEV-phishing-test
	exclude=PRD-PRINTER1

	# exclude using end-of-string - handled as a regex expression
	exclude=PRD-PRINT$

	# exclude PRD-a as well as PRD-a followed by anything (note the use of ".*" instead of "*")
	exclude=PRD-a.*

	# exclude DEV-V followed by anything and ending in TEMP (end-of-string)
	exclude=DEV-V.*TEMP$

	# back up just the root VDI of DEV-web3
	vdi-export=DEV-web3

	# the same as above, except retain seven copies
	vdi-export=DEV-web3:7

	# back up just the root VDI for anything starting with DEV followed by anything, followed
	# by either the string "TEST" or the string "test" followed by anything else
	vdi-export=DEV-.*(TEST|test).*

	# The same as above, except using the string "Test" or "test"
	vdi-export=DEV-.*[Tt]est.*

	# back up VMs ending with the string SAVE and keeping five versions
	vm-export=.*SAVE$:5

	# back up VMs starting with PRD- and ending with print4 or print5 and save five versions
	vm-export=PRD-.*print[4-5]$:5

	# back up VMs starting with PRD- and ending with print6, print7 or print8 and save ten versions
	vm-export=PRD-.*print[6-8]$:10

	# back up VMs starting with PRD- and ending with print followed by any number(s) and ending
	# in that same string of numbers and save eight versions
	vm-export=PRD-.*print[\d{1,}]$:8

Note that there are numerous combinations that may possily conflict with each other or potentially overlap. It is strongly encouraged to use the "preview" option to review the configuration output before putting into service.

### Common cronjob Example

Typically you will want to run the cron with an input config file and redirected output file in case any run time errors occur.

	10 0 * * 6 /usr/bin/python /mnt/VmBackup/VmBackup.py password \
	/mnt/VmBackup/weekly.cfg >> /mnt/VmBackup/logs/VmBackup.log 2>&1

Provide the password for the user `root`. If it contains special characters, make sure to set it in single quotes, e.g. `'your*Password'`.

**Please note:** It is preferred to use the obscured password method instead of passing your plain-text password on the command-line or in a cron job.

### VM selection and max_backups operations

The vm-export and vdi-export each have an associated process list where each entry is of the form vm-name:max_backups. The :max_backups is optional, and if specified then is the maximum number of backups to maintain for this vm-name. Otherwise, the global max_backups is in effect for the given vm-name. At the completion of every successful VM vm-export/vdi-operation, the oldest backup(s) are deleted using the in effect vm-name:max_backups value.

The following VM selection operations apply to the vm-export/vdi-export config: (1) remove any excluded VMs (both simple and regex-based) from the available list of VMs queried from XenServer, (2) load each applicable vdi-export vm into the config for vdi export, then finally (3) load each applicable vm-export vm into the config for full export ignoring any vms already marked for vdi-export. By using the `preview` option then the scope of the given VmBackup run is clearly defined.

For any individual VmBackup.py run, a VM found in the vdi-export list will take precedence over a matching entry in the vm-export list. The convention is that a VM is backed up with a vm-export or a vdi-export, but not both. If at some point in time a VM grows in number of /dev/xvdX disks where it is required to switch from vm-export to vdi-export, then the same %BACKUP_DIR%/vm-name structure continues. Since in this case the backups are ordered by date with a mix of vdi-export and older vm-export backups, eventually the vm-export backups will be deleted. One technique to save any of the older vm-exports from automatically deleting is to simply rename %BACKUP_DIR%/vm-name to %BACKUP_DIR%/vm-name_xva at time of the conversion to vdi-export.
 

### VM Backup Directory Structure

The VM backup directory has this format %BACKUP_DIR%/vm-name/date-time/ and each VM backup directory contains the vm backup file plus additional VM metadata.

Each successful backup directory is marked by a touched file of `success` and in some special cases may include `success_other-actions`. These situations may be reviewed in the VmBackup code.

The number of VM backups saved is based upon the config max_backups value. For example, if max_backups=3 and when the forth successful backup completes, then the oldest backup directory date-time will be deleted.

As each new VM backup begins, then a check is made to ensure that the last VM backup was successful. If it was not successful then the previous failed backup directory will be deleted.

#### VM Backup File Types
The vm backup file has one of three possible formats, (a) vm-name.xva which is created from a vm-export command, (b) vm-name.raw which is created from vdi-export and vdi-export-form=raw, or (c) vm-name.vhd which is created from vdi-export and vdi-export-form=vhd.

#### Additional VM Metadata
For each backup directory, there is a dump of selected XenServer VM metadata. This information can be useful in certain recovery situations.

* vm.cfg - includes name_label, name_description, memory_dynamic_max, VCPUs_max, VCPUs_at_startup, os_version, orig_uuid
* DISK-xvda (for each attached disk)
	* vbd.cfg - includes userdevice, bootable, mode, type, unplugable, empty, orig_uuid
	* vdi.cfg - includes name_label, name_description, virtual_size, type, sharable, read_only, orig_uuid, orig_sr_uuid 
* VIFs (for each attached VIF)
  * vif-0.cfg - includes device, network_name_label, MTU, MAC, other_config, orig_uuid


## Restore
### VM Restore from the vm-export backup
Use the `xe vm-import` command. See `xe help vm-import` for parameter options. In particular, attention should be paid to the "preserve" option, which if specified as `preserve=true` will re-create as many of the original settings as possible, such as the associated VM UUID values along with the network and MAC addresses.

### VDI Restore from the vdi-export backup
Use the `xe vdi-import` command. See `xe help vdi-import` for parameter options. However, the current Citrix documentation is lacking and the best vdi-import examples can be found at http://wiki.xensource.com/wiki/Disk_import/export_APIs

### Pool Restore from the config pool_db_backup=1
If config pool_db_backup=1 has been specified then a %BACKUP_DIR%/METADATA_host-name/pool_db_date-time.dump file will be created. Consult the Citrix XenServer Administrator's Guide chapter 8 and review sections that discuss the `xe pool-restore-database` command.

## Attribution
This project was adapted from [NAUBackup][NAUProject] but has and will continue to grow into something new.

[NAUProject]: https://github.com/NAUBackup/VmBackup
