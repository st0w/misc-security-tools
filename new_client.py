#!/usr/bin/env python
"""Quickly create client certificates for use on a RADIUS server

Ok, some things to note.  This script is HORRIBLY insecure.  You'll see
I don't do ANY input validation or any of that stuff.  Since you're 
meant to run this yourself, I assume you aren't going to pwn yourself.
So with that said, don't do something stupid like hook this up to a web
form or mechanism that allows users to provide arbitrary input.  You'll
break your shit.

Also, there are some race conditions, as I only check for existence of
files in one place and then go on my merry way.  So, use this with
caution.  I'm using this on a box only I have access to, so I've no 
need to build that stuff in at this point.

And finally, the password is passed directly to OpenSSL on the command
line.  Which means, it's visible in things like ps.  Again, I'm the
only user of the box, so I don't care.  A better option would be to
use the subprocess module and setup pipes for stdin/stdout.

Based on Tim Lisko's excellent walk-through at
http://www.privacywonk.net/2010/10/security-how-to-wpa2-enterprise-on-your-home-network.php

"""
# Path to important files
ln = '/bin/ln'
openssl = '/usr/bin/openssl'
basedir = '/etc/certstore'
xpext_file = basedir + '/xpextensions'
opensslcnf = basedir + '/openssl.cnf'
newcerts = basedir + '/newcerts'
exportdir = basedir + '/export'
wireless_basedir = '/etc/wireless'
wireless_certs = wireless_basedir + '/certs/clients'

# XP Extensions to use, from xpext_file
xpext_extensions = 'xpclient_ext'

# Client options
client = ''
client_expire = 1825

# ---*< Imports and functions go here... >*------------------------------------

# System imports
from getpass import getpass
import os

# Third-party imports
# Local imports
# Functions

# ---*< Code goes here... >*---------------------------------------------------

# Check for existence of necessary stuff...
for x in [ln, openssl, basedir, xpext_file, opensslcnf, newcerts,
            wireless_basedir, wireless_certs]:
    if not os.path.exists(x):
        print "%s does not exist, cannot continue." % x
        os._exit(-1)

# Get client name and info
while not client:
    client = raw_input('Enter machine name of client: ')

# Setup filename vars
key_path = '%s/%s_key.pem' % (newcerts, client)
req_path = '%s/%s_req.pem' % (newcerts, client)
cert_path = '%s/%s_cert.pem' % (newcerts, client)
wireless_cert_path = '%s/%s_cert.pem' % (wireless_certs, client)
p12_path = '%s/%s_cert.p12' % (exportdir, client)

# Verify none in existence
for x in [key_path, req_path, cert_path, wireless_cert_path, p12_path]:
    if os.path.exists(x):
        print '%s exists, refusing to overwrite. Resolve and try again.' % x
        os._exit(-1)

winning = raw_input('Windows client [y/N]: ')
winning = winning.upper() == 'Y'

client_expire = raw_input('Enter client cert expiration in days [%d]: ' %
                          client_expire) or client_expire

# I had to patch getpass.py on Solaris to prevent echoing...
# http://bugs.python.org/issue7208
passwd = 'a'
passwd_v = 'b'

while passwd != passwd_v or len(passwd) < 12:
    passwd = getpass('Enter client cert password: ')
    passwd_v = getpass('Verify password: ')
    if passwd != passwd_v:
        print "Error: passwords don't match.  Try again."
    if len(passwd) < 12:
        print "Error: password must be at least twelve chars long"

ca_pass = getpass('Enter the CA password: ')

# Create client cert
print 'Creating client cert...'
create_client = ("%s req -new -keyout %s -out %s -days %s -config %s "
                 "-passout pass:'%s' "
                                 "-subj '/C=US/ST=New York/L=Brooklyn/organizationName=st0w"
                                        "/organizationalUnitName=Security/CN=%s'" %
                 (openssl, key_path, req_path, client_expire, opensslcnf,
                                  passwd, client))
os.system(create_client)

# Sign client cert
print 'Signing client cert...'
sign_client = ("%s ca -config %s -passin pass:'%s' -out %s -days %s "
               "-infiles %s " %
               (openssl, opensslcnf, ca_pass, cert_path, client_expire,
                              req_path))
# Add Windows extensions if needed
if winning:
    sign_client = ('%s -extensions %s -extfile %s' %
                   (sign_client, xpext_extensions, xpext_file))
os.system(sign_client)

# Create a symlink
print 'Creating symlink in %s...' % wireless_certs
link_cert = '%s -s %s %s' % (ln, cert_path, wireless_cert_path)
os.system(link_cert)

# Export cert for the client
print "Exporting client cert"
export_cert = ("%s pkcs12 -export -in %s -inkey %s -out %s -passin pass:'%s' "
               "-passout pass:'%s' -clcerts" %
               (openssl, cert_path, key_path, p12_path, passwd, passwd))
os.system(export_cert)

#print create_client
#print sign_client
#print link_cert
#print export_cert
print "Done! Pick up the new cert from the following and copy to client machine:\n%s" % p12_path
print "Don't forget to import /etc/certstore/export/st0wCA.der first!"
