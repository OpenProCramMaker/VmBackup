#!/usr/bin/python

# VmBackup - XenServer Backup
# Copyright (C) 2017  OnyxFire, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# See README for usage and installation documentation

import logging, sys, argparse, datetime
import vbconfig, vbhelper, vbservice

version = '1.0.1'

def main():
	server_name = h.get_server_name()
	logger.info('----------------------------')
	logger.info('VmBackup running on {}'.format(server_name))
	logger.info('Started: {}'.format(h.get_date_string(False)))
	logger.info('----------------------------')
	logger.info('')
	logger.info('=====================================')
	logger.info('Gathering Pool Information ({})'.format(h.get_time_string()))
	logger.info('=====================================')
	logger.info('')
	logger.info('**** Get All VMs ****')
	all_vms = service.get_all_vms()
	logger.info('')

	logger.info('==============================')
	logger.info('Validating VM lists ({})'.format(h.get_time_string()))
	logger.info('==============================')
	logger.info('')

	excludes = h.validate_vm_list('excludes', config['excludes'], all_vms)
	logger.info('')

	vdi_exports = h.validate_vm_list('vdi-exports', config['vdi_exports'], all_vms)
	logger.info('')

	vm_exports = h.validate_vm_list('vm-exports', config['vm_exports'], all_vms)
	logger.info('')

	# Sort lists for readability and logical ordering of backups
	excludes = sorted(excludes, key=str.lower)
	vdi_exports = sorted(vdi_exports, key=str.lower)
	vm_exports = sorted(vm_exports, key=str.lower)

	if config['preview']:
		h.print_config(config)
		h.print_vm_list('excludes', excludes)
		h.print_vm_list('vdi-exports', vdi_exports)
		h.print_vm_list('vm-exports', vm_exports)
		sys.exit(0)

	logger.info('==========================')
	logger.info('Running Backups ({})'.format(h.get_time_string()))
	logger.info('==========================')
	logger.info('')

	if config['host_backup']:
		service.backup_hosts(config['max_backups'], config['backup_dir'])
		logger.info('')

	if config['pool_backup']:
		service.backup_pool_db(config['max_backups'], config['backup_dir'])
		logger.info('')

	if vdi_exports:
		service.backup_vdi(vdi_exports, config)
		logger.info('')

	if vm_exports:
		service.backup_vm(vm_exports, config)
		logger.info('')

	logger.info('--------------------------------')
	logger.info('Ended: {}'.format(h.get_date_string(False)))

def setup():
	parent_parser = argparse.ArgumentParser(add_help=False)
	parent_parser.add_argument('-c', '--config', help='Config file for runtime overrides', metavar='FILE')
	parent_parser.add_argument('-b', '--base-dir', metavar='PATH',
		help='Base directory (Default: /mnt/VmBackup)' )
	args, remaining_argv = parent_parser.parse_known_args()
	
	cfg = vbconfig.Configurator(h, args)
	options = cfg.configure()
	
	current_year = datetime.datetime.now().year
	copyright = 'Copyright (C) {}  OnyxFire, Inc. <https://onyxfireinc.com>'.format(current_year)
	program_title = 'VmBackup {} - XenServer Backup'.format(version)
	written_by = 'Written by: Lance Fogle (@lancefogle)'
	child_parser = argparse.ArgumentParser(
	  description=program_title + '\n' + copyright + '\n' + written_by,
	  parents=[parent_parser],
	  version=program_title + '\n' + copyright + '\n' + written_by,
	  formatter_class=argparse.RawDescriptionHelpFormatter
	)
	child_parser.set_defaults(**options)
	child_parser.add_argument('-d', '--backup-dir', metavar='PATH',
		help='Backups directory (Default: /mnt/VmBackup/exports)')
	child_parser.add_argument('-p', '--pool-backup', action='store_true', help='Backup Pool DB')
	child_parser.add_argument('-H', '--host-backup', action='store_true', help='Backup Hosts in Pool (dom0)')
	child_parser.add_argument('-l', '--log-level', choices=[ 'debug', 'info', 'warning', 'error', 'critical' ],
		help='Log Level (Default: info)', metavar='LEVEL')
	child_parser.add_argument('-C', '--compress', action='store_true',
		help='Compress on export (vm-exports only)')
	child_parser.add_argument('-F', '--format', choices=[ 'raw', 'vhd' ], metavar='FORMAT',
		help='VDI export format (vdi-exports only, Default: raw)')
	child_parser.add_argument('--preview', action='store_true', help='Preview resulting config and exit')
	child_parser.add_argument('-e', '--vm-export', action='append', dest='vm_exports', metavar='STRING',
		help='VM name or Regex for vm-export (Default: ".*") NOTE: Specify multiple times for multiple values)')
	child_parser.add_argument('-E', '--vdi-export', action='append', dest='vdi_exports', metavar='STRING',
		help='VM name or Regex for vdi-export (Default: None) NOTE: Specify multiple times for multiple values)')
	child_parser.add_argument('-x', '--exclude', action='append', dest='excludes', metavar='STRING',
		help='VM name or Regex to exclude (Default: None) NOTE: Specify multiple times for multiple values)')

	final_args = vars(child_parser.parse_args(remaining_argv))
	options.update(final_args)
	cfg.validate_config(options)
	return options
		
if __name__ == '__main__':
	h = vbhelper.Helper()
	config = setup()
	logger = logging.getLogger('vmbackup')
        if config['log_level']:
                logger.setLevel(getattr(logging, config['log_level'].upper(), None))
	service = vbservice.XenLocalService(h)
	
	try:
		service.get_session()
		main()
	finally:
		service.end_session()
