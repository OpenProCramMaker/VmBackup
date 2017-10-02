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

import datetime, os, re, subprocess
from logging import getLogger
from os import remove, listdir
from os.path import exists, getsize, join, getmtime
from shlex import split

class Helper():

	def __init__(self):
		self.logger = getLogger('vmbackup.helper')

	def delete_file(self, file):
		if exists(file):
			self.logger.debug('(i) File exists, deleting...')
			try:
				remove(file)
				return True
			except OSError as e:
				self.logger.critical('(!) Unable to delete file "{}": {}'.format(file, e))
		else:
			self.logger.debug('(i) File does not exist: {}'.format(file))
		return False

	def get_elapsed(self, start, end, as_string=True):
		difference = end - start
		elapsed = ''
		symbol = ''
		if difference.seconds < 60:
			elapsed = difference.seconds
			symbol = 's'
		elif difference.seconds < 3600:
			elapsed = difference.seconds / 60
			symbol = 'm'
		elif difference.seconds < 86400:
			elapsed = (difference.seconds / 60) / 60
			symbol = 'h'
		else:
			elapsed = difference.days
			symbol = 'd'
		if as_string:
			elapsed = '{}{}'.format(str(elapsed), symbol)
		return elapsed

	def get_file_size(self, file, as_string=True):
		size = 0
		try:
			size = getsize(file) / (1024 * 1024 * 1024)
		except OSError as e:
			self.logger.critical('(!) Unable to get file size: {}'.format(e))
		if as_string:
			size = '{}G'.format(str(size))
		return size

	def get_cmd_result(self, cmd_line, strip_newline=True):
		self.logger.debug('(i) Running command: {}'.format(cmd_line))
		result = ''
		cmd = split(cmd_line)
		try:
			result = subprocess.check_output(cmd)
			if strip_newline:
				result = result.rstrip("\n")
		except subprocess.CalledProcessError:
			self.logger.debug('(!) Command returned with non-zero exit status')
		return result

	def get_date_string(self, file_format=True, date=''):
		if date == '':
			now = datetime.datetime.now()
		else:
			now = date
		if file_format:
			str = '%02d%02d%04d-%02d%02d%02d' \
				% (now.month, now.day, now.year, now.hour, now.minute, now.second)
		else:
			str = '%02d/%02d/%04d %02d:%02d:%02d' \
				% (now.month, now.day, now.year, now.hour, now.minute, now.second)
		return str

	def get_remaining_space(self, filesystem):
		cmd = '/bin/df --output=pcent {}'.format(filesystem)
		fs_info = self.get_cmd_result(cmd)
		try:
			output = fs_info.split('\n')[1][2:-1]
			self.logger.debug('(i) Used space: {}'.format(output))
			percent_used = int(output)
		except ValueError as e:
			self.logger.debug('(i) Unexpectedly returned non-integer; defaulting to 100%')
			percent_used = int(100)
		percent_remaining = 100 - percent_used
		return percent_remaining

	def get_server_name(self):
		return os.uname()[1]

	def get_time_string(self, date=''):
		if not date:
			now = datetime.datetime.now()
		else:
			now = date
		str = '%02d:%02d:%02d' \
			% (now.hour, now.minute, now.second)
		return str

	def is_vm_name(self, text):
		if re.match('^[\w\s\-\_]+$', text) is not None:
			return True
		else:
			return False

	def is_valid_regex(self, text):
		try:
			re.compile(text)
			return True
		except re.error as e:
			self.logger.debug('(i) Regex is not valid: {}'.format(e))
		return False

	def print_config(self, config):
		self.logger.info('VmBackup running with these settings:')
		self.logger.info('  backup_dir        = {}'.format(config['backup_dir']))
		self.logger.info('  space_threshold   = {}'.format(config['space_threshold']))
		self.logger.info('  share_type        = {}'.format(config['share_type']))
		self.logger.info('  compress          = {}'.format(config['compress']))
		self.logger.info('  max_backups       = {}'.format(config['max_backups']))
		self.logger.info('  vdi_export_format = {}'.format(config['vdi_export_format']))
		self.logger.info('  pool_backup       = {}'.format(config['pool_backup']))
		self.logger.info('  host_backup       = {}'.format(config['host_backup']))

	def print_vm_list(self, type, vms):
		self.logger.info('  {} (cnt) = {}'.format(type, len(vms)))
		str = ''
		for vm in vms:
			str += '{}, '.format(vm)
		if len(str) > 1:
			str = str[:-2]
		self.logger.info('  {}: {}'.format(type, str))

	def rotate_backups(self, max, path):
		self.logger.debug('(i) Path to check for backups: {}'.format(path))
		self.logger.debug('(i) Maximum backups to keep: {}'.format(max))
		files = [join(path, f) for f in listdir(path)]
		if len(files) % 2 == 0:
			backups = len(files) / 2
			self.logger.debug('(i) Total backups found: {}'.format(backups))
			files = sorted(files, key=getmtime)
			while (backups > max and backups > 1):
				meta_file = files.pop(0)
				backup_file = files.pop(0)
				self.logger.info('> Removing old metadata backup: {}'.format(meta_file))
				self.logger.info('> Removing old backup: {}'.format(backup_file))
				remove(meta_file)
				remove(backup_file)
				backups -= 1
			return True
		else:
			self.logger.error('(!) Pairs of backup and meta-backups are not even. Please remove orphaned files from {}.'.format(path))
			return False

	def run_cmd(self, cmd_line):
		self.logger.debug('(i) Running command: {}'.format(cmd_line))
		cmd = split(cmd_line)
		FNULL = open(os.devnull, 'w')
		result = subprocess.call(cmd, stdout=FNULL, stderr=subprocess.STDOUT)
		FNULL.close()
		return result

	def validate_vm_list(self, type, list, vms):
		self.logger.info('**** {} ****'.format(type.upper()))
		self.logger.debug('(i) VM List: {}'.format(list))
		validated_list = []
		found_match = False

		# Fail fast if all VMs excluded, no VMs exist in the pool, or
		# list empty to prevent python regex from matching all VMs
		if ( vms == [] or list == [] ):
			self.logger.info('>> Success <<')
			return validated_list

		# Evaluate values if we get this far
		for value in list:
			self.logger.debug('(i) Checking for matches: %s', value)
			values = value.split(':')
			vm_name = values[0]
			vm_backups = ''
			vdi_disks = ''
			if len(values) > 1:
				try:
					tmp_max = int(values[1])
					if isinstance(tmp_max, (int, long)) and (tmp_max == -1 or tmp_max > 0):
						vm_backups = values[1]
						if len(values) == 3:
							vdi_disks = values[2]
					else:
						self.logger.warning('(!) max_backups out of range: {}'.format(values[1]))
				except ValueError as e:
					self.logger.warning('(!) max_backups non-integer: {}'.format(e))
			no_match = []

			# Warn if name/regex not valid and jump to next item in list
			if not self.is_vm_name(vm_name) and not self.is_valid_regex(vm_name):
				self.logger.warning('(!) Invalid regex: {}'.format(vm_name))
				continue

			# Check for matches against VMs in pool and add to final list for backup
			no_match.append(vm_name)
			for vm in vms:
				# Below line for extreme debugging only as pool may have thousands of VMs
				#self.logger.debug('(i) Checking against VM: %s', vm)
				if ((self.is_vm_name(vm_name) and vm_name == vm) or
					(not self.is_vm_name(vm_name) and re.match(vm_name, vm))):
					if vm_backups == '':
						new_value = vm
					elif not vm_backups == '' and not vdi_disks == '':
						new_value = '{}:{}:{}'.format(vm, vm_backups, vdi_disks)
					else:
						new_value = '{}:{}'.format(vm, vm_backups)
					self.logger.debug('(i) Match found: {}'.format(vm))
					found_match = True
					if vm_name in no_match:
						no_match.remove(vm_name)
					validated_list.append(new_value)

			for vm in no_match:
				self.logger.warning('(!) No matching VMs found: {}'.format(vm))

			# Remove matches from master list to prevent duplicates in other lists
			if found_match:
				for vm in validated_list:
					if vm in vms:
						vms.remove(vm)

		if found_match:
			self.logger.info('>> Success <<')
		else:
			self.logger.info('>> Error <<')
		return validated_list

	def verify_path(self, path):
		if not exists(path):
			try:
				os.mkdir(path)
				return True
			except OSError as e:
				self.logger.error('(!) Unable to create directory {} : {}'.format(path, e))
				return False
		return True

	def verify_path_writeable(self, path):
		touchfile = join(path, "write.test")
		cmd = '/bin/touch "{}"'.format(touchfile)
		try:
			result = self.run_cmd(cmd)
			if result <> 0:
				self.logger.error('(!) Command returned non-zero exit status: {}'.format(cmd))
				return False
			else:
				cmd = '/bin/rm -f "{}"'.format(touchfile)
				self.run_cmd(cmd)
				return True
		except OSError as e:
			self.logger.error('(!) Unable to write to directory {}: {}'.format(path, e))
		return False