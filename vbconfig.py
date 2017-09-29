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

import ConfigParser
from json import load
from logging import debug, info, warning, error, critical, getLogger
from logging.config import dictConfig
from os import getenv
from os.path import exists, expanduser

class Configurator(object):
 
	def __init__(self, helper):
		self.h = helper
		self._setup_logging()
		self.logger = getLogger('vmbackup.config')

	def configure(self, args=''):
		log = self.logger
		log.debug('(i) Setting defaults for configuration')
		conf_parser = ConfigParser.SafeConfigParser()
		log.debug('(i) Adding vmbackup section')
		conf_parser.add_section('vmbackup')
		if args.base_dir:
			log.debug('(i) Updating base_dir from command-line args')
			conf_parser.set('vmbackup', 'base_dir', args.base_dir)
		else:
			conf_parser.set('vmbackup', 'base_dir', '/mnt/VmBackup')
		conf_parser.set('vmbackup', 'share_type', 'nfs')
		conf_parser.set('vmbackup', 'backup_dir', '%(base_dir)s/exports')
		conf_parser.set('vmbackup', 'space_threshold', '20')
		conf_parser.set('vmbackup', 'max_backups', '4')
		conf_parser.set('vmbackup', 'compress', 'False')
		conf_parser.set('vmbackup', 'vdi_export_format', 'raw')
		conf_parser.set('vmbackup', 'pool_backup', 'False')
		conf_parser.set('vmbackup', 'host_backup', 'False')
		log.debug('(i) Reading updates to config from configuration files')
		conf_parser.read(['/mnt/VmBackup/etc/vmbackup.cfg', '/etc/vmbackup.cfg', expanduser('~/vmbackup.cfg')])
		if args.config:
			log.debug('(i) Reading configuration file provided on command-line')
			conf_parser.read([args.config])
		log.debug('(i) Done setting configuration from files')
		return self._sanitize_options(conf_parser)

	def _sanitize_options(self, parser):
		log = self.logger
		log.debug('(i) Sanitizing configuration options')
		options = {}

		# vmbackup Settings
		options['base_dir'] = parser.get('vmbackup', 'base_dir')
		options['share_type'] = parser.get('vmbackup', 'share_type')
		if options['share_type'] == 'smb':
			options['backup_dir'] = parser.get('vmbackup', 'backup_dir').replace("/", "\\")
		else:
			options['backup_dir'] =  parser.get('vmbackup', 'backup_dir')
		options['space_threshold'] = parser.getint('vmbackup', 'space_threshold')
		options['max_backups'] = parser.getint('vmbackup', 'max_backups')
		options['compress'] = parser.getboolean('vmbackup', 'compress')
		options['vdi_export_format'] = parser.get('vmbackup', 'vdi_export_format')
		options['pool_backup'] = parser.getboolean('vmbackup', 'pool_backup')
		options['host_backup'] = parser.getboolean('vmbackup', 'host_backup')
		if parser.has_option('vmbackup', 'log_level'):
			options['log_level'] = parser.get('vmbackup', 'log_level')
		options['vm_exports'] = parser.get('vmbackup', 'vm_exports').split(',') if parser.has_option('vmbackup', 'vm_exports') else []
		options['vdi_exports'] = parser.get('vmbackup', 'vdi_exports').split(',') if parser.has_option('vmbackup', 'vdi_exports') else []
		options['excludes'] = parser.get('vmbackup', 'excludes').split(',') if parser.has_option('vmbackup', 'excludes') else []
		log.debug('(i) Done sanitizing options')
		log.debug('(i) Returning sanitized options')
		return options

	def _setup_logging(self):
		debug('(i) Begin logging configuration')
		DEFAULT_LOGGING={
			"version": 1,
			"disable_existing_loggers": False,
			"formatters": {
				"simple": {
					"format": "%(message)s"
				},
				"detailed": {
					"format": "%(asctime)s - %(levelname)s: %(message)s [ %(module)s:%(funcName)s():%(lineno)s ]",
					"datefmt": "%m/%d/%Y %I:%M:%S %p"
				}
			},
			"handlers": {
				"console": {
					"class": "logging.StreamHandler",
					"formatter": "simple",
					"stream": "ext://sys.stdout"
				},
				"file": {
					"class": "logging.handlers.RotatingFileHandler",
					"level": "WARNING",
					"formatter": "detailed",
					"filename": "/mnt/VmBackup/logs/vmbackup.log",
					"maxBytes": 10485760,
					"backupCount": 20,
					"encoding": "utf8"
				},
				"debug": {
					"class": "logging.handlers.RotatingFileHandler",
					"level": "DEBUG",
					"formatter": "detailed",
					"filename": "/mnt/VmBackup/logs/debug.log",
					"maxBytes": 10485760,
					"backupCount": 20,
					"encoding": "utf8"
				}
			},
			"loggers": {
				"vmbackup": {
					"level": "INFO",
					"handlers": ["console", "file", "debug"],
					"propagate": 0
				}
			},
			"root": {
				"level": "WARNING",
				"handlers": ["console"]
			}
		}

		cfg_file = '/mnt/VmBackup/etc/logging.json'
		value = getenv('LOG_CFG', None)
		if value:
			debug('(i) Logging config environment variable set -> {}'.format(value))
			cfg_file = value
		if exists(cfg_file):
			debug('(i) Logging config file exists. Loading...')
			with open(cfg_file, 'r') as f:
				try:
					log_config = load(f)
					dictConfig(log_config)
					debug('(i) Configuration successfully loaded -> {}'.format(cfg_file))
				except Exception as e:
					warning('(!) Error loading logging configuration from file: {}'.format(e))
					debug('(i) Falling back to default configuration')
					dictConfig(DEFAULT_LOGGING)
		else:
			debug('(i) Config file doesn\'t exist: loading default configuration')
			dictConfig(DEFAULT_LOGGING)

	def validate_config(self, options):
		log = self.logger
		log.debug('(i) Validating Configuration options')

		log.debug('(i) Checking if space_threshold within range')
		if options['space_threshold'] < 1:
			log.critical('(!) space_threshold out of range -> {}'.format(options['max_backups']))
			raise ValueError('(!) space_threshold out of range -> {}'.format(options['space_threshold']))

		log.debug('(i) Checking if max_backups within range')
		if options['max_backups'] < 1:
			log.critical('(!) max_backups out of range -> {}'.format(options['max_backups']))
			raise ValueError('(!) max_backups out of range -> {}'.format(options['max_backups']))

		log.debug('(i) Checking if vdi_export_format is valid value')
		if options['vdi_export_format'] != 'raw' and options['vdi_export_format'] != 'vhd':
			log.critical('(!) vdi_export_format invalid -> {}'.format(options['vdi_export_format']))
			raise ValueError('(!) vdi_export_format invalid -> {}'.format(options['vdi_export_format']))

		log.debug('(i) Checking if backup_dir exists')
		if not exists(options['backup_dir']):
			log.critical('(!) backup_dir does not exist -> {}'.format(options['backup_dir']))
			raise ValueError('(!) backup_dir does not exist -> {}'.format(options['backup_dir']))
		else:
			log.debug('(i) Checking if backup_dir writeable')
			if not self.h.verify_path_writeable(options['backup_dir']):
				log.critical('(!) backup_dir not writeable -> {}'.format(options['backup_dir']))
				raise ValueError('(!) backup_dir not writeable -> {}'.format(options['backup_dir']))

		log.debug('(i) Checking if both vm_exports and vdi_exports are empty')
		if ( not options['vm_exports'] ) and ( not options['vdi_exports'] ):
			log.debug('(i) Setting vm_export to default .* (all VMs)')
			options['vm_exports'] = ['.*']