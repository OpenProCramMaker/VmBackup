# VmBackup
XenServer Backup

## Overview
 - The VmBackup tool is run from a XenServer host and utilizes the native `xe vm-export` and `xe vdi-export` commands to backup both Linux and Windows VMs. 
 - The backup is run after a respective vm-snapshot or vdi-snapshot occurs, which allows for the backup to execute while the VM is up and running.
 - During the backup of specified VMs, this tool collects additional VM metadata using the XenServer XenAPI. This additional information can be useful during VM restore situations and is stored in ".meta" files.
 - Typically, VmBackup is implemented through scheduled crontab entries or can be run manually on a XenServer ssh session. It is important to keep in mind that the backup process does use critical dom0 resources, so running a backup during heavy workloads should be avoided (especially if used with `compress` option).
 - The SRs where one or more VDIs are located require sufficient free space to hold a complete snapshot of a VM. The temporary snapshots that are created during the backup process are deleted after the backup has completed.

## Quick Start Checklist

1. VmBackup will require lots of file storage; setup a storage server with an exported VM backup share.
   - Frequently NFS is used for the storage server, with many installation and configuration sources available on the web.
   - An optional SMB/CIFS mode can be enabled via the `share_type` option in the config file.
2. For all of the XenServers in a given pool, mount the new share at your desired filesystem location (default location is `/mnt/VmBackup`). 
3. Finish creating a share directory structure that meets your needs. Here are the VmBackup sub-directories:
   - /mnt/VmBackup/exports - Contains all VM backups (reconfigurable with `backup_dir` option)
   - /mnt/VmBackup/etc - Contains optional configuration file `vmbackup.cfg` for overriding default configuration and optional `logging.json` for overriding default logging settings
   - /mnt/VmBackup/logs - Contains VmBackup log files `vmbackup.log` and `debug.log`.
4. Download and extract the latest release to your execution location, such as `/mnt/VmBackup`
5. Inspect and customize certain options in the `/mnt/VmBackup/etc/vmbackup.cfg`, `/etc/vmbackup.cfg`, and/or `~/vmbackup.cfg` as desired. `/mnt/VmBackup/etc/vmbackup.example` is heavily commented to help you understand the options. `/mnt/VmBackup/etc/logging.example` shows the default logging configuration.
   - The configuration files are read in the following order with a "last match wins" convention
     - `/mnt/VmBackup/etc/vmbackup.cfg`
     - `/etc/vmbackup.cfg`
     - `~/vmbackup.cfg`
     - Command-line specified config file using `-c <file>` or `--config <file>` option
6. Initially use the `--preview` command-line option to confirm the resulting configuration from files and command-line flags before running an actual backup.
7. Set up a crontab entry or method for executing backups on a schedule

## VmBackup Command Usage

#### Basic usage:

VmBackup.py [-h] [-v] [-c FILE] [-b PATH] [-d PATH] [-p] [-H] [-l LEVEL] [-C] [-F FORMAT] [--preview] [-e STRING]  
   [-E STRING] [-x STRING]  

optional arguments:  
   `-h, --help`  show this help message and exit  
   `-v, --version`  show program's version number and exit  
   `-c FILE, --config FILE`  Config file for runtime overrides  
   `-b PATH, --base-dir PATH`  Base directory (Default: /mnt/VmBackup)  
   `-d PATH, --backup-dir PATH`  Backups directory (Default: /mnt/VmBackup/exports)  
   `-p, --pool-backup`  Backup Pool DB  
   `-H, --host-backup`  Backup Hosts in Pool (dom0)  
   `-l LEVEL, --log-level LEVEL`  Log Level (Default: info)  
   `-C, --compress`  Compress on export (vm-exports only)  
   `-F FORMAT, --format FORMAT`  VDI export format (vdi-exports only, Default: raw)  
   `--preview`  Preview resulting config and exit  
   `-x STRING, --exclude STRING`  VM name or Regex to exclude (Default: None) NOTE: Specify multiple times for multiple values)
   `-e STRING, --vm-export STRING`  VM name or Regex for vm-export (Default: ".*") NOTE: Specify multiple times for multiple values)  
   `-E STRING, --vdi-export STRING`  VM name or Regex for vdi-export (Default: None) NOTE: Specify multiple times for multiple values) 

#### Some usage examples:

	# Backup all VMs in the pool
	./VmBackup.py

	# Backup a single VM by name (case sensitive)
	./VmBackup.py  -e DEV-MYSQL
	
	# Backup a single VM by name with spaces in name
	./VmBackup.py -e "DEV MYSQL"
	
	# Backup VMs by regex which matches more than one VM
	./VmBackup.py -e DEV-MY.*
	
	# Backup VM by name and keep last 2 backups (overrides max_backups)
	./VmBackup.py  -e DEV-MYSQL:2

	# Export just first disk (xvda) for a single VM by name
	./VmBackup.py -E DEV-MYSQL
	
	# Export just xvdb disk from a single VM by name without overriding number of backups to keep
	./VmBackup.py -E DEV-MYSQL:-1:xvdb
	
	# Export 2 disks of a VM by name and keep last 7 backups
	./VmBackup.py -E DEV-MYSQL:7:xvda;xvdb

### A few words about Python REGEX syntax

For the handling of wildcard VMs, VmBackup incorporates the native python regex library of regular expressions. **WARNING:** The syntax is slightly different from what is processed with the Linux family of grep commands. In python, a string followed by `*` causes the resulting regular expression to match zero or more repetitions of the preceding regular expression, as many repetitions as are possible. For example, `ab*` will match "a", "ab", or "a" followed by any number of "b" characters. Therefore, if you had PRD-a*, this will match PRD-a, PRD-aa, PRD-aaaSomething, as well as PRD- but _also_ PRD-Test, PRD-123 and anything else starting with PRD- since zero occurences of the "a" after the "-" are matched. To avoid this, PRD-a.* should be used, instead, indicating in this case PRD-a followed by any single character (".") zero or more("*") times.

Note that the current implementation uses the re.match function which by design is expected to be front-anchored. You can explicitly preface a search string with the "^" operator, if desired, but it is already implied and the results will be the same.

A VM name is considered to be a simple (non-wildcard) name, provided that it contains only combinations of any of the following: letters (upper as well as lower case), numerals 0 through 9, the space character, hyphens (dashes), and underscore characters. These will _not be handled using regex operations_!

### Configuration
Configuration of backups follows the below order of precendence and lower precedence matches will not match the same VM already matched by a higher precedence match:
1. Excludes
2. VDI Exports (just disk)
3. VM Exports (full backup)

#### Examples of configuration file syntax for VMs to backup

Exclude simple host names (non-wildcard instances)  
`excludes = DEV-phishing-test,PRD-PRINTER1`

Exclude using end-of-string - handled as a regex expression  
`excludes = PRD-PRINT$`

Exclude PRD-a as well as PRD-a followed by anything (note the use of ".*" instead of "*")  
`excludes = PRD-a.*`

Exclude DEV-V followed by anything and ending in TEMP (end-of-string)  
`excludes = DEV-V.*TEMP$`

Backup just the root VDI of DEV-web3  
`vdi_exports = DEV-web3`

Same as above, except retain seven copies  
`vdi_exports = DEV-web3:7`
	
Same again except use default max backups and backup first two disks (note semi-colon separator)  
`vdi_exports = DEV-web3:-1:xvda;xvdb`

Backup just the root VDI for anything starting with DEV followed by anything, followed  
by either the string "TEST" or the string "test" followed by anything else and also backup a  
specific VM  
`vdi_exports = DEV-.*(TEST|test).*,DEV-EUWWW01`

Same as above, except using the string "Test" or "test"  
`vdi_exports = DEV-.*[Tt]est.*`

Backup VMs ending with the string SAVE and keep five backups  
`vm_exports = .*SAVE$:5`

Backup VMs starting with PRD- and ending with print4 or print5 and save five backups and  
backup another specific VM and keep only 2 backups  
`vm_exports = PRD-.*print[4-5]$:5,DEV-USWWW05:2`

Backup VMs starting with PRD- and ending with print6, print7 or print8 and save ten versions  
`vm_exports = PRD-.*print[6-8]$:10`

Backup VMs starting with PRD- and ending with print followed by any number(s) and ending  
in that same string of numbers and save eight versions  
`vm_exports = PRD-.*print[\d{1,}]$:8`

Note that there are numerous combinations that may possibly conflict with each other or potentially overlap. It is strongly encouraged to use the `--preview` option to review the configuration output before putting into service. Also note that `excludes`, `vdi_exports`, and `vm_exports` options should only be specified once each in the configuration files with multiple values being comma-separated.

### Common cronjob examples

Run backup once a week with no report  
`10 0 * * 6 /mnt/VmBackup/VmBackup.py >>/dev/null 2>&1`

Run backup once a week and let cron send email with output on every run  
`10 0 * * 6 /mnt/VmBackup/VmBackup.py`

Run backup once a week and let cron send email only if there are warnings or errors  
`10 0 * * 6 /mnt/VmBackup/VmBackup.py -l warning`

Run backup of all VMs nightly and backup pool metadata and hosts weekly with full report emailed by cron  
```
  10 0 * * * /mnt/VmBackup/VmBackup.py
  10 0 * * 6 /mnt/VmBackup/VmBackup.py -x '.*' -p -H
```

NOTE: Configuring your system to send emails from cron to your email is well-documented for linux hosts and is outside the scope of this document

### VM selection and max_backups operations

The number of VM backups saved is based upon the configured max_backups value. For example, if max_backups=3 and the fourth successful backup completes, the oldest backup will be deleted. The vm_exports and vdi_exports each have their associated process list where each entry is of the form vm-name/regex:max_backups. The :max_backups is optional, and, if specified, is the maximum number of backups to maintain for this vm-name. Otherwise, the global max_backups is in effect for the given vm-name. At the completion of every successful VM vm-export/vdi-export operation, the oldest backup(s) are deleted using the in effect vm-name:max_backups value. If you want to specify specific disks to backup during a vdi-export, you must specify the max_backups field; if you do not want to deviate from the configured setting just use -1 as the value (i.e. `VMNAME:-1:xvdb;xvdc`). **WARNING**: Each VDI backed up using vdi-export counts as a backup, even if for the same VM so keep this in mind if you specify multiple disks for a VM (i.e. MYVM03:2:xvda;xvdb will only keep one backup of each disk since together they total 2 backups).

The following VM selection operations apply to the vm-export/vdi-export configuration (both command-line and config file selections): (1) Remove any matched VMs from excludes (both simple and regex-based) from the available list of VMs in the pool, (2) load each matched VM in vdi_exports into the config for vdi-export, then finally (3) load each matched VM from vm_exports into the config for full export ignoring any VMs already marked for vdi-export. By using the `--preview` option the scope of the given VmBackup run is clearly output and is a good way to test.

For any individual VmBackup run, a VM found in the vdi-export list will take precedence over a matching entry in the vm-export list. The convention is that a VM is backed up with a vm-export or a vdi-export, but not both. If at some point in time a VM grows in number of /dev/xvdX disks where it is required to switch from vm-export to vdi-export, then the same %BACKUP_DIR%/vm-name structure continues. Since in this case the backups are ordered by date with a mix of vdi-export and older vm-export backups, eventually the vm-export backups will be deleted.

### VM Backup Directory Structure

The VM backup directory has this format %BACKUP_DIR%/vm-name/ and each VM backup directory contains the vm backup files plus backup metadata files from each backup.

#### VM Backup File Types
The vm backup file has one of four possible formats, (1) backup_[date]-[time].xva which is created from a vm-export, (2) backup_[date]-[time].xva.gz created from a vm-export with `compress` option, (3) backup_[date]-[time].raw which is created from vdi-export in raw format, or (4) backup_[date]-[time].vhd which is created from vdi-export in vhd format.

#### Additional VM Metadata
For each backup, there is a dump of selected XenServer VM metadata in a backup_[date]-[time].meta file. This information can be useful in certain recovery situations.

* VM
	* name_label, name_description, memory_dynamic_max, VCPUs_max, VCPUs_at_startup, os_version, orig_uuid
* DISK (for each attached disk)
	* device, userdevice, bootable, mode, type, unplugable, empty, orig_uuid
	* VDI
		* name_label, name_description, virtual_size, type, sharable, read_only, orig_uuid, orig_sr_uuid 
* VIFs (for each attached VIF)
  * device, network_name_label, MTU, MAC, other_config, orig_uuid

## Restore
### VM Restore from the vm-export backup
Use the `xe vm-import` command. See `xe help vm-import` for parameter options. In particular, attention should be paid to the "preserve" option, which if specified as `preserve=true` will re-create as many of the original settings as possible, such as the associated VM UUID values along with the network and MAC addresses.

### VDI Restore from the vdi-export backup
Use the `xe vdi-import` command. See `xe help vdi-import` for parameter options. The current Citrix documentation is lacking and the best vdi-import examples can be found at http://wiki.xensource.com/wiki/Disk_import/export_APIs

### Pool DB Restore
Consult the Citrix XenServer Administrator's Guide chapter 8 and review sections that discuss the `xe pool-restore-database` command.  
   * If `pool_backup` option has been specified then a %BACKUP_DIR%/POOL_DB/metadata_[date]-[time].db file will be created.

### Host Backup Restore
Use the `xe host-restore` command. See `xe help host-restore` for parameter options.  
   * If `host_backup` option has been specified then a %BACKUP_DIR%/HOSTS/hosts_[date]-[time].xbk file will be created.

## Attribution
This project was adapted from [NAUBackup][NAUProject] but has and will continue to grow into something new.

[NAUProject]: https://github.com/NAUBackup/VmBackup
