#!/usr/bin/python

import re, sys, os, json, random, string
from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import curdir, sep

def generate_key(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    
MY_PORT = 9000
USE_KEY = false
API_KEY = generate_key(16)
CFG_PATH = os.path.dirname(os.path.realpath(__file__))
print "Automatically generated API Key: " + API_KEY

#===================================================================
# Function that sets the LED state:
#===================================================================
def led_state(s):
	try:
		f = open("/proc/acpi/nuc_led", "w")
		f.write(s)
		f.close()
		return True
	except IOError:
		print "Error accessing the /proc/acpi/nuc_led module!"
		return False

#===================================================================
# Function that saves the module parameters to a file:
#===================================================================
def save_module_params():
	params = ""
	try:
		f = open("/sys/module/nuc_led/parameters/nuc_led_profiles", "r")
		params = f.read()
		f.close()
	except IOError:
		print "Warning: Unable to read profile string from module!"
		return False
	try:
		f = open(CFG_PATH + "/led_server.cfg", "w")
		f.write(params)
		f.close()
		return True
	except IOError:
		print "Warning: Unable to write configuration file to \"led_server.cfg!\"!"
		return False

#===================================================================
# Function that loads the module parameters from a file:
#===================================================================
def load_module_params():
	try:
		f.open(CFG_PATH + "/led_server.cfg", "r")
		line = f.readline()
		while line:
			led_state(line)
		f.close()
		return True
	except IOError:
		print "Warning: Configuration file not available!"
		return False

class myHandler(BaseHTTPRequestHandler):
	#===================================================================
	# Handler for the GET requests
	#===================================================================
	def do_GET(self):
		
		#===================================================================
		# Are we trying to save the module parameters?
		#===================================================================
		if self.path.startswith("/api/save?"):
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			params = parse_qs(urlparse(self.path).query)
			api = str(params.get("api", None))
			api = api.replace('[', '').replace(']', '').replace("'", "")
			if not USE_KEY or api == API_KEY:
				if save_module_params():
					self.wfile.write("Module configuration saved to file!")
				else:
					self.wfile.write("Unable to save module configuration to file!")
			else:
				self.wfile.write("Invalid API key")
			return

		#===================================================================
		# Are we trying to load the module parameters?
		#===================================================================
		if self.path.startswith("/api/load?"):
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			params = parse_qs(urlparse(self.path).query)
			api = str(params.get("api", None))
			api = api.replace('[', '').replace(']', '').replace("'", "")
			if not USE_KEY or api == API_KEY:
				if load_module_params():
					self.wfile.write("Module configuration loaded from file!")
				else:
					self.wfile.write("Unable to load module configuration from file!")
			else:
				self.wfile.write("Invalid API key")
			return

		#===================================================================
		# Are we trying to change the LED settings or profiles?
		#===================================================================
		elif self.path.startswith("/api/set?"):
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			params = parse_qs(urlparse(self.path).query)
			api = str(params.get("api", None))
			api = api.replace('[', '').replace(']', '').replace("'", "")
			if not USE_KEY or api == API_KEY:
				which = str(params.get("which", None))
				bright = str(params.get("brightness", params.get("bright", 100)))
				fade = str(params.get("fade", "none"))
				color = str(params.get("color", "none"))
				profile = str(params.get("profile", "current"))
				s = which + "," + bright + "," + fade + "," + color
				if profile <> "current":
					s = s + "," + profile
				s = s.replace("[", "").replace("]", "").replace("'", "")
				
				# Attempt to change the LED settings or profile:
				if led_state(s):
					self.wfile.write("Parameters passed to kernel module: " + s)
				else:
					self.wfile.write("Error accessing /proc/acpi/nuc_led to set LED state")
			else:
				self.wfile.write("Invalid API key")
			return
			
		#===================================================================
		# Are we trying to change the LED settings or profiles?
		#===================================================================
		elif self.path.startswith("/api/get?"):
			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			params = parse_qs(urlparse(self.path).query)
			api = str(params.get("api", None))
			api = api.replace('[', '').replace(']', '').replace("'", "")
			if not USE_KEY or api == API_KEY:
				profile = str(params.get("profile", "current"))
				profile = profile.replace("'", "").replace("[", "").replace("]", "")
				
				# Attempt to change the LED settings or profile to view:
				if profile <> "current":
					if not led_state('view,' + profile):
						return
			
				# Attempt to read the LED settings or profile:
				try:
					f = open("/sys/module/nuc_led/parameters/nuc_led_profiles", "r")
					output = f.read()
					f.close()
				except IOError:
					self.wfile.write("Error accessing /proc/acpi/nuc_led to get LED state")
					return
			
				# Parse the output into an array for the JavaScript:
				arr = {}

				# Parse the Power LED settings:
				if arr["power"]["enabled"]:
					numbers = re.findall("(\d+|ffffffff)", split[0])

					# Brightness of Power LED:
					try:
						arr["power"]["brightness"] = int(numbers[0])
					except ValueError:
						arr["power"]["brightness"] = -1

					# Fade setting of Power LED:
					try:
						arr["power"]["fade"] = int(numbers[1])
					except ValueError:
						arr["power"]["fade"] = -1

					# Color of Power LED:
					try:
						arr["power"]["color"] = int(numbers[2])
					except ValueError:
						arr["power"]["color"] = -1

				# Parse the Ring LED settings:
				if arr["ring"]["enabled"]:
					numbers = re.findall("(\d+|ffffffff)", split[0])

					# Brightness of ring LED:
					try:
						arr["ring"]["brightness"] = int(numbers[0])
					except ValueError:
						arr["ring"]["brightness"] = -1

					# Fade setting of ring LED:
					try:
						arr["ring"]["fade"] = int(numbers[1])
					except ValueError:
						arr["ring"]["fade"] = -1

					# Color of ring LED:
					try:
						arr["ring"]["color"] = int(numbers[2])
					except ValueError:
						arr["ring"]["color"] = -1

				# Pass the built array as a JSON response:
				self.wfile.write(json.dumps(arr))
			else:
				self.wfile.write("Invalid API key")
			return

		#===================================================================
		# Or should we return the API key for website usage?
		#===================================================================
		elif self.path  ==  "/js/api_key.js":
			self.send_response(200)
			self.send_header('Content-type', "text/javascript")
			self.end_headers()
			self.wfile.write("set API_KEY=" + API_KEY)
			return
		
		#===================================================================
		# Or should we change LED profile to "recording mode"?
		#===================================================================
		elif self.path  ==  "/profile/recording":
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			if not self.voice:
				if led_state("profile,recording"):
					self.wfile.write("Recording profile activated")
			else:
				self.wfile.write("Recording profile queued to activate")
			self.last_mode = "recording"
			return
		
		#===================================================================
		# Or should we change LED profile to "boot mode"?
		#===================================================================
		elif self.path  ==  "/profile/boot":
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			if not self.voice:
				if led_state("profile,boot"):
					self.wfile.write("Boot profile activated")
			else:
				self.wfile.write("Boot profile queued to activate")
			self.last_mode = "boot"
			return
			
		#===================================================================
		# Or should we change the LED profile to "voice" profile?
		#===================================================================
		elif self.path  ==  "/profile/voice":
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			if not self.voice:
				if led_state("profile,recording"):
					self.wfile.write("Voice profile activated")
				else:
					self.wfile.write("Voice profile already activated")
			self.voice = True
			return
		
		#===================================================================
		# Or should we change the LED profile back to the previous profile?
		#===================================================================
		elif self.path  ==  "/profile/normal":
			self.send_response(200)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			if not self.voice:
				if led_state("profile," + self.last_mode):
					if self.last_mode  ==  "recording":
						self.wfile.write("Recording profile activated")
					else:
						self.wfile.write("Boot profile activated")
			else:
				self.wfile.write("Voice profile not activated")
			self.voice = False;
			return
			
		#===================================================================
		# None of the static functions were requested.  Return a static file:
		#===================================================================
		# If no filename specified, assume "index.html":
		if self.path  ==  "/":
			self.path = "/index.html"
		
		# Check the file extension required and set the right mime type:
		if self.path.endswith(".jpg"):
			mimetype = 'image/jpg'
		elif self.path.endswith(".gif"):
			mimetype = 'image/gif'
		elif self.path.endswith(".js"):
			mimetype = 'application/javascript'
		elif self.path.endswith(".css"):
			mimetype = 'text/css'
		else:
			mimetype = 'text/html'
			
		# Open the static file requested and send it:
		try:
			f = open(curdir + sep + self.path) 
			buffer = f.read()
			f.close()
			self.send_response(200)
			self.send_header('Content-type', mimetype)
			self.end_headers()
			self.wfile.write(buffer)
		except IOError:
			self.send_response(404)
			self.send_header('Content-type', "text/html")
			self.end_headers()
			self.wfile.write("<html><head><title>404 File Not Found</title></head><body bgcolor = \"white\"><center><h1>404 File Not Found</h1></center><hr></body></html>")
		return

#===================================================================
# Try to load the NUC_LED module with the specified parameters:
#===================================================================
try:
	f = open("/proc/acpi/nuc_led", "r")
	data = f.read()
	f.close()
	load_module_params()
except IOError:
	uid = os.getuid()
	gid = os.getgid()
	# Load the WMI module before trying to load the NUC LED module:
	os.system("modprobe wmi")
	# Load the NUC LED module now:
	s = "modprobe nuc_led nuc_led_perms=664 nuc_led_gid=" + str(uid) + " nuc_led_uid=" + str(gid)
	os.system(s)
	# Try to load the saved configuration into the module:
	if not load_module_params():
		print "Error: /proc/acpi/nuc_led kernel module cannot be loaded!  Aborting!"
		sys.exit(1)

#===================================================================
# Set the LED profile to "boot".  Abort the script if this fails:
#===================================================================
if not led_state("profile,boot"):
	sys.exit(1)

#===================================================================
# Create web server & define the handler to manage the incoming request
#===================================================================
try:
	myHandler.voice = False
	myHandler.last_mode = "boot"
	server = HTTPServer(('', MY_PORT), myHandler)
	print 'Started httpserver on port ' , MY_PORT
	server.serve_forever()

except KeyboardInterrupt:
	save_module_params()
	print "Shutting down the web server"
	server.socket.close()
	sys.exit(0)
