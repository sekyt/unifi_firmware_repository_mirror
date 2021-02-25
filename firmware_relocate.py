#!/usr/bin/python3

import json
import re
import os
import urllib.parse
import copy
import hashlib
import requests
import yaml

def canonizeControllerVersion(str_controller_version):
	v = str_controller_version.split('.')
	out = ''
	for a in v:
		 out = out + '{:0>10}'.format(a)
	return(out)

def md5(filename):
	def file_as_bytes(file):
		with file:
			return file.read()

	return(hashlib.md5(file_as_bytes(open(filename, 'rb'))).hexdigest())

def take_second(elem):
	return(elem[1])

class unifiFirmware:
	def __init__(self, str_controller_version, stream, model, attrs):
		self.controller_version = canonizeControllerVersion(str_controller_version)
		self.controller_version_raw = str_controller_version
		self.stream = stream
		self.model = model
		self.attrs = attrs
		self.new_url = self.attrs['url']

	def print(self):
		print(self.controller_version, self.stream, self.model, self.attrs)
		print(self.getURLprotocol())
		print(self.getURLserver())
		print(self.getURLpath())
		print(self.getURLdir())
		print(self.getURLfilename())
		print(self.new_url)

	def getURLprotocol(self):
		o = urllib.parse.urlparse(self.attrs['url'])
		return(o.scheme)

	def getURLserver(self):
		o = urllib.parse.urlparse(self.attrs['url'])
		return(o.hostname)

	def getURLpath(self):
		o = urllib.parse.urlparse(self.attrs['url'])
		return(o.path)

	def getURLdir(self):
		path = self.getURLpath()
		m = re.match('^/(.*)/', path)
		if m:
			return(m.group(1))
		else:
			return(None)

	def getURLfilename(self):
		path = self.getURLpath()
		m = re.match('.*/([^/][^/]*)', path)
		if m:
			return(m.group(1))
		else:
			return(None)

	def transformURL(self, protocol=None, server=None, path=None):
		if not protocol:
			protocol = self.getURLprotocol()
		if not server:
			server = self.getURLserver()
		if not path:
			path = self.getURLpath()
			
		self.new_url = protocol + '://' + server + path

	def download(self, basedir='.', proxies = {}):
		d = basedir + '/' + self.getURLdir()
		f = d + '/' + self.getURLfilename()
		os.makedirs(d, exist_ok = True)
		r = requests.get(self.attrs['url'], verify=True, proxies=proxies)
		fout = open(f, 'wb')
		fout.write(r.content)
		fout.close()

		cmd5 = md5(f)
		if cmd5 == self.attrs['md5sum']:
			print('DL OK, md5sums OK')


class unifiFirmwares:
	def __init__(self, config_file = 'firmware_relocate.yml'):

		self.process_config_file(config_file)

		fin = open(self.cfg['source_firmware_json_file'], 'r')
		self.jsdata = json.load(fin)
		fin.close()

		self.firmwares = []
		self.cversions = []

		# go thru controller versions
		for cversion in self.jsdata.keys():
			if cversion == 'last_changed':
				self.last_changed = self.jsdata['last_changed']

			if cversion == 'last_checked':
				self.last_checked = self.jsdata['last_checked']

			if isinstance(self.jsdata[cversion], dict):
				self.cversions.append([cversion, canonizeControllerVersion(cversion)])
				for stream in self.jsdata[cversion].keys():
					for model in self.jsdata[cversion][stream].keys():
						f = unifiFirmware(cversion, stream, model, self.jsdata[cversion][stream][model])
						self.firmwares.append(f)
		self.cversions.sort(key=take_second)
		print('Controller versions in', self.cfg['source_firmware_json_file'], ':')
		print(self.cversions)

	def process_config_file(self, config_file):
		self.cfg = {}
		try:
			with open(config_file, 'r') as stream:
				config = yaml.safe_load(stream)
		except FileNotFoundError:
			print('! Config file ' + config_File + ' not found !')
			return(False)
		except yaml.scanner.ScannerError:
			print('! Parsing of .yml config file ' + config_file + ' failed !')
			return(False)

		# defaults:
		self.cfg['source_firmware_json_file'] = 'firmware.json-ubnt'
		self.cfg['destination_firmware_json_file'] = 'firmware.json'
		self.cfg['transformURL'] = { 'protocol': None, 'server': None, 'path': None }
		self.cfg['firmware_base_directory'] = 'firmware_repo'
		self.cfg['proxies'] = {}
		self.cfg['filter'] = {'version': None, 'model': None}

		# set values
		if 'source_firmware_json_file' in config.keys():
			self.cfg['source_firmware_json_file'] = config['source_firmware_json_file']

		if 'destination_firmware_json_file' in config.keys():
			self.cfg['destination_firmware_json_file'] = config['destination_firmware_json_file']

		if 'transformURL' in config.keys():
			for a in ['protocol', 'server', 'path']:
				if a in config['transformURL'].keys():
					self.cfg['transformURL'][a] = config['transformURL'][a]

		if 'firmware_base_directory' in config.keys():
			self.cfg['firmware_base_directory'] = config['firmware_base_directory']

		if 'proxies' in config.keys():
			self.cfg['proxies'] = config['proxies']

		if 'filter' in config.keys():
			for a in ['version', 'model']:
				if a in config['filter'].keys():
					self.cfg['filter'][a] = config['filter'][a]
		print('Configuration:')
		print(self.cfg)

	def print(self):
		for a in self.firmwares:
			a.print()

	def findFirmware(self, cversion, stream, model):
		for a in self.firmwares:
			if a.controller_version == cversion and a.stream == stream and a.model == model:
				return(a)
		return(None)

	def transformURL(self):
		jsdata = copy.deepcopy(self.jsdata)
		for f in self.firmwares:
			f.transformURL(self.cfg['transformURL']['protocol'],
			               self.cfg['transformURL']['server'],
			               self.cfg['transformURL']['path'])
			jsdata[f.controller_version_raw][f.stream][f.model]['url'] = f.new_url
		fout = open(self.cfg['destination_firmware_json_file'], 'w')
		fout.write(json.dumps(jsdata, sort_keys=True, indent=4))
		fout.close()
		print('Transformed file', self.cfg['destination_firmware_json_file'], 'created.')
			
	def download(self):
		total_fw = len(self.firmwares)
	
		for a in range(total_fw):

			if not self.cfg['filter']['version']:
				filter_version_expr = True
			else:
				filter_version_expr = (self.firmwares[a].controller_version in map(canonizeControllerVersion, self.cfg['filter']['version']))
			if not self.cfg['filter']['model']:
				filter_model_expr = True
			else:
				filter_model_expr = (self.firmwares[a].model in self.cfg['filter']['model'])

			if filter_version_expr and filter_model_expr:
				print('Download ', a + 1, '/', total_fw, ":\n",
					  'controller version:', self.firmwares[a].controller_version_raw, "\n",
					  'model:', self.firmwares[a].model, "\n",
					  'URL:', self.firmwares[a].attrs['url'])
				self.firmwares[a].download(basedir=self.cfg['firmware_base_directory'],
				                           proxies=self.cfg['proxies'])

		print('Download done.')

fs = unifiFirmwares()
fs.transformURL()
fs.download()
