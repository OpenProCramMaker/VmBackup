# Changelog for VmBackup

## v1.1.0 - 5 October 2017
 - [enhancements]
 	* Removed redundant check for previous snapshot as not required if using `snapshot-list`/`snapshot-destroy`
 - [new features]
 	* Auto-detects base directory based upon VmBackup.py run location
 - [important notes]
 	* `base_dir` option is no longer configurable as it is no longer required

## v1.0.2 - 4 October 2017
 - [enhancements]
 	* Documentation update for sSMTP configuration
	* Minor Documentation updates for clarification/typos
	* Removed pool-db-backup check if running on master (no longer required)
	* Removed unused method and params

## v1.0.1 - 2 October 2017
 - [bugs]
	* Fixed issue with multiple hosts for host-backup
	* Removed backup rotations for host-backup as would need code rework

## v1.0.0 - 2 October 2017
 - [enhancements]
	* Complete refactor of code with emphasis on code reuse
	* No code changes required to override settings of any kind
	* Proper type checking on config load
	* More configuration file override options with an order of
		precendence to allow for very flexible override capabilities
	* Configurable logging with logging module
	* Uses argparse for handling command-line arguments
	* OO principles implemented - new modular design
	* Emphasis on simplicity of use with no required arguments to run
	* Uses local xapi socket to communicate so doesn't need credentials
		while running locally on XenServer host
	* Singular metadata backup file per backup
	* No per-backup directories
	* Backup rotation for host-backup and pool-db-backup
	* No email code - instead relies on host to send email from cron if configured
	* Able to control verbosity of email reports as desired using log-level flags
	* Improved logging messages and formatting for easy to read logs/reports
 - [new features]
	* Host-backup
	* Backup directory space threshold
	* Disk selection for VDI exports
	* Log level control to affect desired output
 - [bugs]
	* Many minor bug fixes during refactor
 

## v0.0.1 - 12 September 2017
 - Initial Release, pending concrete "API"
