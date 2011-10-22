#!/usr/bin/env python
# ---*< bitly_grinder/bitly_grinder.py >*-------------------------------------
# Copyright (C) 2011 st0w
# 
# This module is part of project and is released under the MIT License.
# Please see the LICENSE file for details.

"""Grinds random bit.ly URLs looking for interesting info

Created on Oct 22, 2011

By default, will follow sequential URLs.  This is to allow for starting
and stopping without hitting the same URL twice.

Works recursively.  Start with a URL, it keeps following redirects until
getting something other than 301/302.


Thoughts:
* Track the resulting document type, so can easily view non-HTML

"""
# ---*< Standard imports >*---------------------------------------------------
from random import choice
import sys
import urllib2

# ---*< Third-party imports >*------------------------------------------------

# ---*< Local imports >*------------------------------------------------------
from db import init_db_conn, save_result
from models import BitlyUrl

# ---*< Initialization >*-----------------------------------------------------
USER_AGENTS = [
    'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) '
    'AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b '
    'Safari/531.21.102011-10-16 20:23:50',

    'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.3) Gecko/20100401 '
    'Firefox/3.6.3 (FM Scene 4.6.1)',

    'Mozilla/4.0 (compatible; MSIE 5.0; Windows ME) Opera 5.11 [en]',

    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.1) '
    'Gecko/2008092215 Firefox/3.0.1 Orca/1.1 beta 3',

    'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-US) AppleWebKit/xx '
    '(KHTML like Gecko) OmniWeb/v5xx.xx',

    '',
]


# ---*< Code >*---------------------------------------------------------------
def resolve_url(db, url):
    """Resolves a URL to its final destination URL
    
    This will rescursively call itself until the status is anything
    other than 301 or 302.
    
    :param db: `SQLite3` db handle
    :param url: `string` containing the URL to resolve
    :rtype: `tuple` in the format (`int`, `string`).  The `string` is
            the final URL in the resolution process, and the `int` is
            the status code obtained when trying to access it.

    """
    headers = {
        'User-Agent': choice(USER_AGENTS),
    }

    req = urllib2.Request(url, headers=headers)

    try:
        resp = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        return (e.code, url, url)

    if resp.getcode() in (301, 302):
        print 'recursing'
        return resolve_url(db, resp.geturl())

    return (resp.getcode(), url, resp.geturl())


def main(url):
    """Simple wrapper, just calls the resolver for now
    
    Drops the last letter of the passed `url` and then grabs all URLs
    that start with the remaining `string`
    
    :param url: `string` of the base URL to start with
    :rtype: None
    
    """
    db = init_db_conn()

    base_url = url[:-1]
    for i in range(97, 123):
        bitly = BitlyUrl(base_url='%s%s' % (base_url, chr(i)))

        (bitly.status,
         bitly.base_url,
         bitly.resolved_url) = resolve_url(db, bitly.base_url)

        if bitly.status != 404:
            sys.stdout.write('%d %s\t-> %s\n' % (bitly.status, bitly.base_url,
                                             bitly.resolved_url))
        save_result(db, bitly)


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.stderr.write('Usage: %s url\n' % sys.argv[0])
        sys.exit(1)

    main(sys.argv[1])

__all__ = ()
