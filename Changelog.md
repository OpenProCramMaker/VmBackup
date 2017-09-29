# Changelog for VmBackup

## v1.0.0 - ?? October 2017
 - [general improvements]
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
 - [new features]
	* Host backup
	* Backup directory space threshold
	* Disk selection for VDI exports
	* Log level control to affect desired output
 - [bugs fixed]
	* Many minor bug fixes during refactor
 

## v0.0.1 - 12 September 2017
 - Initial Release, pending concrete "API"