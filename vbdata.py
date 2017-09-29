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

from logging import getLogger
import XenAPI

class DataAPI(object):

	def __init__(self, session):
		self.logger = getLogger('vmbackup.data')
		self.session = session
		self.sx = self.session.xenapi

	def get_network_record(self, network):
		self.logger.debug('(i) Getting record for Network: {}'.format(network))
		network_record = self.sx.network.get_record(network)
		return network_record

	def get_sr_record(self, sr):
		self.logger.debug('(i) Getting record for SR: {}'.format(sr))
		sr_record = self.sx.SR.get_record(sr)
		return sr_record

	def get_vbd_record(self, vbd):
		self.logger.debug('(i) Getting record for VBD: {}'.format(vbd))
		vbd_record = self.sx.VBD.get_record(vbd)
		return vbd_record

	def get_vdi_record(self, vdi):
		self.logger.debug('(i) Getting record for VDI: {}'.format(vdi))
		vdi_record = self.sx.VDI.get_record(vdi)
		return vdi_record

	def get_vif_record(self, vif):
		self.logger.debug('(i) Getting record for VIF: {}'.format(vif))
		vif_record = self.sx.VIF.get_record(vif)
		return vif_record

	def get_vm_by_name(self, vm_name):
		self.logger.debug('(i) Getting VM object: {}'.format(vm_name))
		vm = self.sx.VM.get_by_name_label(vm_name)
		return vm  

	def get_vm_record(self, vm):
		self.logger.debug('(i) Getting record for VM: {}'.format(vm))
		vm_record = self.sx.VM.get_record(vm)
		return vm_record

	def login(self):
		raise NotImplementedError('(!) Must be overriden in subclass')

	def logout(self):
		self.logger.debug('(i) Logging out of session')
		self.sx.session.logout()

	def vm_exists(self, vm_name):
		self.logger.debug('(i) Checking if vm exists: {}'.format(vm_name))
		vm = self.sx.VM.get_by_name_label(vm_name)
		if ( len(vm) == 0 ):
			return False
		else:
			return True

class XenLocal(DataAPI):

	def __init__(self):
		session = XenAPI.xapi_local()
		super(self.__class__, self).__init__(session)

	def login(self):
		self.logger.debug('(i) Logging in to get session')
		self.sx.login_with_password('root', '', '2.7', 'VmBackup')

class XenRemote(DataAPI):

	def __init__(self, username, password, url):
		self.username = username
		self.password = password
		self.url = url
		session = XenAPI.Session('https:)//' + self.url)
		super(self.__class__, self).__init__(session)

	def login(self):
		self.logger.debug('(i) Logging in to get session')
		self.sx.login_with_password(self.username, self.password, '2.7', 'VmBackup')