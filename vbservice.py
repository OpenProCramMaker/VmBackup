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

import datetime
from logging import getLogger
from os.path import join
import vbdata

class Service(object):

	def __init__(self, helper, data):
		self.logger = getLogger('vmbackup.service')
		self.h = helper
		self.d = data

	def backup_hosts(self, file):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def backup_pool_db(self, backup_dir):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def backup_meta(self, vm_record, meta_file):
		# Create dictionary to return all VDI devices and their uuids for vdi-exports
		vdi_data = {}

		self.logger.debug('(i) Opening metadata file for writing')
		meta_out = open(meta_file, 'w')

		# Get VM metadata
		self.logger.debug('(i) Recording VM metadata: {}'.format(vm_record['name_label']))
		meta_out.write('******* VM *******\n')
		meta_out.write('name_label={}\n'.format(vm_record['name_label']))
		meta_out.write('name_description={}\n'.format(vm_record['name_description']))
		meta_out.write('memory_dynamic_max={}\n'.format(vm_record['memory_dynamic_max']))
		meta_out.write('VCPUs_max={}\n'.format(vm_record['VCPUs_max']))
		meta_out.write('VCPUs_at_startup={}\n'.format(vm_record['VCPUs_at_startup']))
		if vm_record['other_config']['base_template_name']:
			meta_out.write('base_template_name={}\n'.format(vm_record['other_config']['base_template_name']))
		meta_out.write('os_version={}\n'.format(self.get_os_version(vm_record['uuid'])))
		meta_out.write('orig_uuid={}\n'.format(vm_record['uuid']))
		meta_out.write('\n')
		self.logger.debug('(i) VM metadata recorded: {}'.format(vm_record['name_label']))

		# Get VM disk metadata
		for vbd in vm_record['VBDs']:
			vbd_record = self.d.get_vbd_record(vbd)
			if vbd_record['type'].lower() != 'disk':
				self.logger.debug('(i) Not a disk... skipping: {}'.format(vbd_record['type']))
				continue

			vdi_record = self.d.get_vdi_record(vbd_record['VDI'])

			# Store VDI device:uuid pairs for vdi-exports
			self.logger.debug('(i) Storing VDI metadata: {}:{}'.format(vbd_record['device'], vdi_record['uuid']))
			vdi_data[vbd_record['device']] = vdi_record['uuid']

			self.logger.debug('(i) Recording DISK metadata: {}'.format(vbd_record['device']))
			meta_out.write('******* DISK *******\n')
			meta_out.write('device={}\n'.format(vbd_record['device']))
			meta_out.write('userdevice={}\n'.format(vbd_record['userdevice']))
			meta_out.write('bootable={}\n'.format(vbd_record['bootable']))
			meta_out.write('mode={}\n'.format(vbd_record['mode']))
			meta_out.write('type={}\n'.format(vbd_record['type']))
			meta_out.write('unpluggable={}\n'.format(vbd_record['unpluggable']))
			meta_out.write('empty={}\n'.format(vbd_record['empty']))
			meta_out.write('orig_uuid={}\n'.format(vbd_record['uuid']))
			self.logger.debug('(i) Recording vdi metadata: {}'.format(vdi_record['name_label']))
			meta_out.write('---- VDI ----\n')
			meta_out.write('name_label={}\n'.format(vdi_record['name_label']))
			meta_out.write('name_description={}\n'.format(vdi_record['name_description']))
			meta_out.write('virtual_size={}\n'.format(vdi_record['virtual_size']))
			meta_out.write('type={}\n'.format(vdi_record['type']))
			meta_out.write('sharable={}\n'.format(vdi_record['sharable']))
			meta_out.write('read_only={}\n'.format(vdi_record['read_only']))
			meta_out.write('orig_uuid={}\n'.format(vdi_record['uuid']))
			sr_uuid = self.d.get_sr_record(vdi_record['SR'])['uuid']
			meta_out.write('orig_sr_uuid={}\n'.format(sr_uuid))
			self.logger.debug('(i) VDI metadata recorded: {}'.format(vdi_record['name_label']))
			meta_out.write('\n')
			self.logger.debug('(i) Disk metadata recorded: {}'.format(vbd_record['device']))

		# Get VM VIF metadata
		for vif in vm_record['VIFs']:
			vif_record = self.d.get_vif_record(vif)
			self.logger.debug('(i) Recording VIF metadata: {}'.format(vif_record['device']))
			meta_out.write('******* VIF *******\n')
			meta_out.write('device={}\n'.format(vif_record['device']))
			network_name = self.d.get_network_record(vif_record['network'])['name_label']
			meta_out.write('network_name_label={}\n'.format(network_name))
			meta_out.write('MTU={}\n'.format(vif_record['MTU']))
			meta_out.write('MAC={}\n'.format(vif_record['MAC']))
			meta_out.write('other_config={}\n'.format(vif_record['other_config']))
			meta_out.write('orig_uuid={}\n'.format(vif_record['uuid']))
			meta_out.write('\n')
			self.logger.debug('(i) VIF metadata recorded: {}'.format(vif_record['device']))

		self.logger.debug('(i) Closing metadata file')
		meta_out.close()

		self.logger.debug('(i) Stored VDI data: {}'.format(vdi_data))
		return vdi_data

	def backup_vdi(self, vms, config):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def backup_vm(self, vms, config):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def end_session(self):
		self.d.logout()

	def get_all_hosts(self, as_list=True):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def get_all_vms(self, as_list=True):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def get_os_version(self, uuid):
		raise NotImplementedError('(!) Must be implemented in subclass')

	def get_session(self):
		self.d.login()

	def get_vm_by_name(self, vm_name):
		vm = self.d.get_vm_by_name(vm_name)
		# Return nothing if more than one VM has same name
		if len(vm) > 1:
			self.logger.error('(!) More than one VM exists with same name: {}'.format(vm_name))
			vm = []
			return vm
		else:
			return vm[0]

	def is_master(self):
		raise NotImplementedError('(!) Must be implemented in subclass')

class XenLocalService(Service):

	def __init__(self, helper):
		self._xe_path = '/opt/xensource/bin'
		super(self.__class__, self).__init__(helper, vbdata.XenLocal())

	def backup_hosts(self, backup_dir, enabled_only=True):
		self.logger.info('** HOST(dom0) BACKUP **')
		if not self.is_master():
			self.logger.error('(!) Unable to backup hosts: Must be run on master.')
		else:
			path = join(backup_dir, 'HOSTS')
			if self.h.verify_path(path):
				backup_file = '{}/hosts_{}.xbk'.format(path, self.h.get_date_string())
				params = ''
				if enabled_only:
					params = 'enabled=true'
				cmd = 'host-backup file-name="{}" --multiple {}'.format(backup_file, params)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to backup hosts')
					self.logger.info('>> Error <<')
				else:
					self.logger.info('>> Success <<')
			else:
				self.logger.critical('(!) Unable to create backup directory: {}'.format(path))
				self.logger.info('>> Error <<')

	def backup_pool_db(self, backup_dir):
		self.logger.info('** POOL DB BACKUP **')
		if not self.is_master():
			self.logger.error('(!) Unable to backup pool db: Must be run on master.')
		else:
			path = join(backup_dir, 'POOL_DB')
			if self.h.verify_path(path):
				backup_file = '{}/metadata_{}.db'.format(path, self.h.get_date_string())
				cmd = 'pool-dump-database file-name="{}"'.format(backup_file)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to backup pool db')
					self.logger.info('>> Error <<')
				else:
					self.logger.info('>> Success <<')
			else:
				self.logger.critical('(!) Unable to create backup directory: {}'.format(path))
				self.logger.info('>> Error <<')

	def backup_vdi(self, vms, config):
		begin_time = datetime.datetime.now()
		self.logger.info('*************************')
		self.logger.info('** VDI-EXPORT ({})'.format(self.h.get_time_string(begin_time)))
		self.logger.info('*************************')
		success_cnt = 0
		error_cnt = 0
		warning_cnt = 0

		self.logger.debug('(i) VMs: {}'.format(vms))

		# Warn if empty list given
		if vms == []:
			self.logger.warning('(!) No VMs selected for vdi-export')
			warning_cnt += 1

		for value in vms:
			vm_start = datetime.datetime.now()
			values = value.split(':')
			vm_name = values[0]
			vm_backups = config['max_backups']
			vdi_disks = ['xvda']
			if len(values) > 1:
				if not values[1] == '-1':
					vm_backups = int(values[1])
			if len(values) == 3:
				vdi_disks[:] = []
				vdi_disks += values[2].split(';')

			self.logger.info('{} started at {}'.format(vm_name, self.h.get_time_string(vm_start)))
			self.logger.debug('(i) Name:{} Max-Backups:{} Disks:{}'.format(vm_name, vm_backups, vdi_disks))
			
			# Check remaining disk space for backup directory against threshold
			self.logger.info('-> Checking backup space')
			backup_space_remaining = self.h.get_remaining_space(config['backup_dir'])
			self.logger.debug('(i) Backup space remaining "{}": {}%'.format(config['backup_dir'], backup_space_remaining))
			if backup_space_remaining < config['space_threshold']:
				self.logger.critical('(!) Space remaining is below threshold: {}%'.format(backup_space_remaining))
				error_cnt += 1
				break

			# Fail if no disks selected for backup
			if not vdi_disks:
				self.logger.error('(!) No disks selected for backup: {}'.format(vm_name))
				error_cnt += 1
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Get VM by name for backup
			vm_object = self.get_vm_by_name(vm_name)
			if not vm_object:
				self.logger.error('(!) No valid VM found: {}'.format(vm_name))
				error_cnt += 1
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			vm_backup_dir = join(config['backup_dir'], vm_name)

			# Create/Verify backup directory 
			if not self.h.verify_path(vm_backup_dir):
				self.logger.error('(!) Unable to create backup directory: {}'.format(vm_backup_dir))
				error_cnt += 1
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Get VM metadata
			self.logger.info('-> Getting VM metadata')
			vm_meta = self.d.get_vm_record(vm_object)
			if not vm_meta:
				self.logger.error('(!) No VM record returned: {}'.format(vm_name))
				error_cnt += 1
				self.logger.info('-> Skipping VDI due to error: {}'.format(vm_name))
				continue

			for disk in vdi_disks:
				vdi_start = datetime.datetime.now()
				self.logger.info('* Begin {} at {}'.format(disk, self.h.get_time_string(vdi_start)))
				
				# Check remaining disk space for backup directory against threshold
				self.logger.info('-> Checking backup space')
				backup_space_remaining = self.h.get_remaining_space(config['backup_dir'])
				self.logger.debug('(i) Backup space remaining "{}": {}%'.format(config['backup_dir'], backup_space_remaining))
				if backup_space_remaining < config['space_threshold']:
					self.logger.critical('(!) Space remaining is below threshold: {}%'.format(backup_space_remaining))
					error_cnt += 1
					break
				
				# Set backup files
				base = '{}/backup_{}_{}'.format(vm_backup_dir, disk, self.h.get_date_string())
				meta_backup_file = '{}.meta'.format(base)
				self.logger.debug('(i) meta_backup_file: {}'.format(meta_backup_file))
				backup_file = '{}.{}'.format(base, config['vdi_export_format'])
				self.logger.debug('(i) backup_file: {}'.format(backup_file))
				snap_name = 'VMBACKUP_{}_{}'.format(vm_name, disk)

				# Backing up VM Metadata
				self.logger.info('-> Backing up VM metadata')
				vdi_data = self.backup_meta(vm_meta, meta_backup_file)

				# Cleanup snapshot from previous attempt if exists
				self.logger.info('-> Checking for previous snapshot: {}'.format(snap_name))
				cmd = 'vdi-list name-label="{}" params=uuid --minimal'.format(snap_name)
				old_snap = self._get_xe_cmd_result(cmd)
				if old_snap:
					self.logger.warning('(!) Previous backup snapshot found: {}'.format(old_snap))
					self.logger.info('> Cleaning up snapshot from previous attempt: {}'.format(snap_name))
					cmd = 'vdi-destroy uuid={}'.format(old_snap)
					if not self._run_xe_cmd(cmd):
						self.logger.error('(!) Failed to cleanup snapshot from previous attempt')
						warning_cnt += 1
					else:
						self.logger.info('> Previous backup snapshot removed')

				# Check for valid disk and get UUID for backup
				self.logger.info('-> Verifying disk is valid: {}'.format(disk))
				if disk in vdi_data:
					vdi_uuid = vdi_data[disk]
				else:
					self.logger.error('(!) Invalid device specified: {}'.format(disk))
					error_cnt += 1
					if not self.h.delete_file(meta_backup_file):
						self.logger.error('(!) Failed to remove metadata file: {}'.format(meta_backup_file))
					self.logger.info('-> Skipping VDI due to error: {}'.format(disk))
					continue

				# Take snapshot of VDI
				self.logger.info('-> Taking snapshot of disk')
				cmd = 'vdi-snapshot uuid={}'.format(vdi_uuid)
				snap_uuid = self._get_xe_cmd_result(cmd)
				if not snap_uuid:
					self.logger.error('(!) Failed to create snapshot: {}'.format(snap_name))
					error_cnt += 1
					self.logger.debug('(i) Removing metadata file: {}'.format(meta_backup_file))
					if not self.h.delete_file(meta_backup_file):
						self.logger.error('(!) Failed to remove metadata file: {}'.format(meta_backup_file))
					self.logger.info('-> Skipping VDI due to error: {}'.format(vm_name))
					continue

				# Set VDI params for easy cleanup
				self.logger.info('-> Setting VDI params')
				cmd = 'vdi-param-set uuid={} name-label="{}"'.format(snap_uuid, snap_name)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to prepare snapshot for backup')
					error_cnt += 1
					self.logger.debug('(i) Destroying snapshot: {}'.format(snap_name))
					cmd = 'vdi-destroy uuid={}'.format(snap_uuid)
					if not self._run_xe_cmd(cmd):
						self.logger.error('(!) Failed to destroy snapshot: {}'.format(snap_name))
					self.logger.info('-> Skipping VDI due to error: {}'.format(vm_name))
					continue

				# Backup VDI from snapshot
				self.logger.info('-> Backing up VDI')
				cmd = 'vdi-export format={} uuid={} filename="{}"'.format(config['vdi_export_format'], snap_uuid, backup_file)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to backup VDI: {}'.format(disk))
					error_cnt += 1
					self.logger.debug('(i) Destroying snapshot: {}'.format(snap_name))
					cmd = 'vdi-destroy uuid={}'.format(snap_uuid)
					if not self._run_xe_cmd(cmd):
						self.logger.error('(!) Failed to destroy snapshot: {}'.format(snap_name))
					self.logger.info('-> Skipping VDI due to error: {}'.format(vm_name))
					continue

				# Remove snapshot now that backup completed
				self.logger.info('-> Cleaning up snapshot: {}'.format(snap_name))
				cmd = 'vdi-destroy uuid={}'.format(snap_uuid)
				if not self._run_xe_cmd(cmd):
					self.logger.warning('(!) Failed to cleanup snapshot: {}'.format(snap_name))
					# Non-fatal so only warning as backup completed but cleanup failed
					warning_cnt += 1

				# Remove old backups based on retention
				self.logger.info('-> Rotating backups')
				if not self.h.rotate_backups(vm_backups, vm_backup_dir):
					self.logger.warning('(!) Failed to cleanup old backups')
					# Non-fatal so only warning as backup completed but cleanup failed
					warning_cnt += 1

				# Gather additional information on backup and report success
				vdi_end = datetime.datetime.now()
				elapsed = self.h.get_elapsed(vdi_start, vdi_end)
				backup_file_size = self.h.get_file_size(backup_file)
				self.logger.info('* End {} at {} - time:{} size:{}'.format(disk, self.h.get_time_string(vdi_end), elapsed, backup_file_size))
				success_cnt += 1

			# VM Summary
			vm_end = datetime.datetime.now()
			elapsed = self.h.get_elapsed(vm_start, vm_end)
			self.logger.info('{} completed at {} - time:{}'.format(vm_name, self.h.get_time_string(vm_end), elapsed))

		# VDI-Export Summary
		end_time = datetime.datetime.now()
		elapsed = self.h.get_elapsed(begin_time, end_time)
		self.logger.info('*************************')
		self.logger.info('VDI-EXPORT completed at {} - time:{}'.format(self.h.get_time_string(end_time), elapsed))

		# Report summary status
		self.logger.info('Summary - S:{} W:{} E:{}'.format(success_cnt, warning_cnt, error_cnt))
		if error_cnt > 0 and success_cnt > 0:
			self.logger.info('>> Success with Errors <<')
		elif warning_cnt > 0 and success_cnt > 0:
			self.logger.info('>> Success with Warning <<')
		elif error_cnt > 0:
			self.logger.info('>> Error <<')
		elif warning_cnt > 0:
			self.logger.info('>> Warning <<')
		elif success_cnt > 0:
			self.logger.info('>> Success <<')
		else:
			# Should never occur
			self.logger.info('>> Unknown <<')

	def backup_vm(self, vms, config):
		begin_time = datetime.datetime.now()
		self.logger.info('************************')
		self.logger.info('** VM-EXPORT ({})'.format(self.h.get_time_string(begin_time)))
		self.logger.info('************************')
		success_cnt = 0
		error_cnt = 0
		warning_cnt = 0

		self.logger.debug('(i) VMs: {}'.format(vms))

		# Warn if empty list given
		if vms == []:
			self.logger.warning('(!) No VMs selected for vm-export')
			warning_cnt += 1

		for value in vms:
			vm_start = datetime.datetime.now()
			values = value.split(':')
			vm_name = values[0]
			vm_backups = config['max_backups']
			if len(values) > 1:
				if not values[1] == -1:
					vm_backups = int(values[1])

			self.logger.info('{} started at {}'.format(vm_name, self.h.get_time_string(vm_start)))
			self.logger.debug('(i) Name:{} Max-Backups:{}'.format(vm_name, vm_backups))

			# Check remaining disk space for backup directory against threshold
			self.logger.info('-> Checking backup space')
			backup_space_remaining = self.h.get_remaining_space(config['backup_dir'])
			self.logger.debug('(i) Backup space remaining: {}%'.format(backup_space_remaining))
			if backup_space_remaining < config['space_threshold']:
				self.logger.critical('(!) Space remaining is below threshold: {}%'.format(backup_space_remaining))
				error_cnt += 1
				break

			# Get VM by name for backup
			vm_object = self.get_vm_by_name(vm_name)
			if not vm_object:
				self.logger.error('(!) No valid VM found: {}'.format(vm_name))
				error_cnt += 1
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Set backup files and destinations
			vm_backup_dir = join(config['backup_dir'], vm_name)			
			base = '{}/backup_{}'.format(vm_backup_dir, self.h.get_date_string())
			meta_backup_file = '{}.meta'.format(base)
			self.logger.debug('(i) meta_backup_file:{}'.format(meta_backup_file))
			if config['compress']:
				backup_file = '{}.xva.gz'.format(base)
			else:
				backup_file = '{}.xva'.format(base)
			self.logger.debug('(i) backup_file:{}'.format(backup_file))

			snap_name = 'VMBACKUP_{}'.format(vm_name)

			# Create/Verify backup directory 
			if not self.h.verify_path(vm_backup_dir):
				self.logger.error('(!) Unable to create backup directory: {}'.format(vm_backup_dir))
				error_cnt += 1
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Get VM metadata
			self.logger.info('-> Getting VM metadata')
			vm_meta = self.d.get_vm_record(vm_object)
			if not vm_meta:
				self.logger.error('(!) No VM record returned: {}'.format(vm_name))
				error_cnt += 1
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Backing up VM Metadata
			self.logger.info('-> Backing up VM metadata')
			self.backup_meta(vm_meta, meta_backup_file)
			
			# Cleanup snapshot from previous attempt if exists
			self.logger.info('-> Checking for previous snapshot: {}'.format(snap_name))
			cmd = 'vm-list name-label="{}" params=uuid --minimal'.format(snap_name)
			old_snap = self._get_xe_cmd_result(cmd)
			if old_snap:
				self.logger.warning('(!) Previous backup snapshot found: {}'.format(old_snap))
				self.logger.info('> Cleaning up snapshot from previous attempt')
				cmd = 'snapshot-destroy uuid={}'.format(old_snap)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to cleanup snapshot from previous attempt')
					warning_cnt += 1
				else:
					self.logger.info('> Previous backup snapshot removed')
			else:
				cmd = 'snapshot-list name-label="{}" params=uuid --minimal'.format(snap_name)
				old_snap = self._get_xe_cmd_result(cmd)
				if old_snap:
					self.logger.warning('(!) Previous backup snapshot found: {}'.format(old_snap))
					self.logger.info('> Cleaning up snapshot from previous attempt')
					cmd = 'snapshot-destroy uuid={}'.format(old_snap)
					if not self._run_xe_cmd(cmd):
						self.logger.error('(!) Failed to cleanup snapshot from previous attempt')
						warning_cnt += 1
					else:
						self.logger.info('> Previous backup snapshot removed')

			vm_uuid = vm_meta['uuid']
			
			# Take snapshot of VM
			self.logger.info('-> Taking snapshot of VM')
			cmd = 'vm-snapshot vm={} new-name-label="{}"'.format(vm_uuid, snap_name)
			snap_uuid = self._get_xe_cmd_result(cmd)
			if not snap_uuid:
				self.logger.error('(!) Failed to create snapshot: {}'.format(snap_name))
				error_cnt += 1
				self.logger.debug('(i) Removing metadata file: {}'.format(meta_backup_file))
				if not self.h.delete_file(meta_backup_file):
					self.logger.error('(!) Failed to remove metadata file: {}'.format(meta_backup_file))
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Prepare snapshot for backup
			self.logger.info('-> Setting VM params')
			cmd = 'template-param-set is-a-template=false ha-always-run=false uuid={}'.format(snap_uuid)
			if not self._run_xe_cmd(cmd):
				self.logger.error('(!) Failed to prepare snapshot for backup')
				error_cnt += 1
				self.logger.debug('(i) Destroying snapshot: {}'.format(snap_name))
				cmd = 'snapshot-destroy uuid={}'.format(snap_uuid)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to destroy snapshot: {}'.format(snap_name))
				self.logger.debug('(i) Removing metadata file: {}'.format(meta_backup_file))
				if not self.h.delete_file(meta_backup_file):
					self.logger.error('(!) Failed to remove metadata file: {}'.format(meta_backup_file))
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Backup VM from snapshot
			self.logger.info('-> Backing up VM')
			cmd = 'vm-export uuid={} filename="{}" compress={}'.format(snap_uuid, backup_file, config['compress'])
			if not self._run_xe_cmd(cmd):
				self.logger.error('(!) Failed to backup VM: {}'.format(vm_name))
				error_cnt += 1
				self.logger.debug('(i) Destroying snapshot: {}'.format(snap_name))
				cmd = 'snapshot-destroy uuid={}'.format(snap_uuid)
				if not self._run_xe_cmd(cmd):
					self.logger.error('(!) Failed to destroy snapshot: {}'.format(snap_name))
				self.logger.debug('(i) Removing metadata file: {}'.format(meta_backup_file))
				if not self.h.delete_file(meta_backup_file):
					self.logger.error('(!) Failed to remove metadata file: {}'.format(meta_backup_file))
				self.logger.info('-> Skipping VM due to error: {}'.format(vm_name))
				continue

			# Remove snapshot now that backup completed
			self.logger.info('-> Cleaning up snapshot')
			cmd = 'vm-uninstall uuid={} force=true'.format(snap_uuid)
			if not self._run_xe_cmd(cmd):
				self.logger.warning('(!) Failed to cleanup snapshot: {}'.format(snap_name))
				# Non-fatal so only warning as backup completed but cleanup failed
				warning_cnt += 1

			# Remove old backups based on retention
			self.logger.info('-> Rotating backups')
			if not self.h.rotate_backups(vm_backups, vm_backup_dir):
				self.logger.warning('(!) Failed to cleanup old backups')
				# Non-fatal so only warning as backup completed but cleanup failed
				warning_cnt += 1

			# Gather additional information on backup and report success
			vm_end = datetime.datetime.now()
			elapsed = self.h.get_elapsed(vm_start, vm_end)
			backup_file_size = self.h.get_file_size(backup_file)
			self.logger.info('{} completed at {} - time:{}'.format(vm_name, self.h.get_time_string(vm_end), elapsed))
			success_cnt += 1

		# VM-Export Summary
		end_time = datetime.datetime.now()
		elapsed = self.h.get_elapsed(begin_time, end_time)
		self.logger.info('*************************')
		self.logger.info('VM-EXPORT completed at {} - time:{}'.format(self.h.get_time_string(end_time), elapsed))

		# Report summary status
		self.logger.info('Summary - S:{} W:{} E:{}'.format(success_cnt, warning_cnt, error_cnt))
		if error_cnt > 0 and success_cnt > 0:
			self.logger.info('>> Success with Errors <<')
		elif warning_cnt > 0 and success_cnt > 0:
			self.logger.info('>> Success with Warning <<')
		elif error_cnt > 0:
			self.logger.info('>> Error <<')
		elif warning_cnt > 0:
			self.logger.info('>> Warning <<')
		elif success_cnt > 0:
			self.logger.info('>> Success <<')
		else:
			# Should never occur
			self.logger.info('>> Unknown <<')

	def get_all_hosts(self, as_list=True):
		cmd = 'host-list params=hostname --minimal'
		hosts = self._get_xe_cmd_result(cmd)
		if as_list:
			hosts = hosts.split(',')
		self.logger.debug('(i) Hosts: {}'.format(hosts))
		if len(hosts) == 0:
			self.logger.error('(!) No hosts returned from pool')
			self.logger.info('>> Error <<')
			raise RuntimeError('(!) No hosts returned from pool')
		else:
			self.logger.info('>> Success <<')
			return hosts

	def get_all_vms(self, as_list=True):
		cmd = 'vm-list is-control-domain=false is-a-snapshot=false params=name-label --minimal'
		vms = self._get_xe_cmd_result(cmd)
		if as_list:
			vms = vms.split(',')
		self.logger.debug('(i) VMs: {}'.format(vms))
		if len(vms) == 0:
			self.logger.error('(!) No VMs in pool to backup')
			self.logger.info('>> Error <<')
			raise RuntimeError('(!) No VMs in pool to backup')
		else:
			self.logger.info('>> Success <<')
			return vms

	def get_os_version(self, uuid):
		cmd = 'vm-list uuid={} params=os-version --minimal'.format(uuid)
		os_version = self._get_xe_cmd_result(cmd)
		if os_version:
			os_version = os_version.split(';')[0][6:]
			self.logger.debug('(i) OS version: {}'.format(os_version))
			return os_version
		else:
			self.logger.debug('(i) OS version empty')
			return 'None'

	def _get_xe_cmd_result(self, cmd):
		cmd = '{}/xe {}'.format(self._xe_path, cmd)
		output = ''
		try:
			output = self.h.get_cmd_result(cmd)
			if output == '':
				self.logger.debug('(i) Command returned no output')
			else:
				self.logger.debug('(i) Command output: {}'.format(output))
		except OSError as e:
			self.logger.critical('(!) Unable to run command: {}'.format(e))
		return output

	def is_master(self):
		self.logger.debug('(i) Checking if host is master')
		try:
			f = open('/etc/xensource/pool.conf', 'r')
			check = f.readline()
			f.close()
			self.logger.debug('(i) Server Status: {}'.format(check))
			if check == 'master':
				return True
		except IOError as e:
			self.logger.critical('(!) Unable to determine master status: {}'.format(e))
		return False

	def _run_xe_cmd(self, cmd):
		cmd = '{}/xe {}'.format(self._xe_path, cmd)
		try:
			result = self.h.run_cmd(cmd)
			if result <> 0:
				self.logger.debug('(!) Command returned non-zero exit status')
			else:
				self.logger.debug('(i) Command successful')
				return True
		except OSError as e:
			self.logger.critical('(!) Unable to run command: {}'.format(e))
		return False

class XenRemoteService(Service):
	pass