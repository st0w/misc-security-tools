#!/usr/bin/env python
# ---*< bitly_grinder/grinder_http_server.py >*-------------------------------
# Copyright (C) 2011 st0w
# 
# This module is part of bit.ly Grinder and is released under the MIT License.
# Please see the LICENSE file for details.
#
"""Quick and dirty HTTP server for browsing results

Created on Oct 22, 2011

"""
# ---*< Standard imports >*---------------------------------------------------
import BaseHTTPServer
import SocketServer

# ---*< Third-party imports >*------------------------------------------------

# ---*< Local imports >*------------------------------------------------------
from db import get_results, init_db_conn
from models import BitlyUrl

# ---*< Initialization >*-----------------------------------------------------
PORT = 8000

# ---*< Code >*---------------------------------------------------------------
class BGHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """Simple GET handler for bit.ly grinder"""
    def do_GET(self):
        # Not the most efficient way to connect to the DB, would be
        # better to connect once and retain, but, I'm lazy.
        db = init_db_conn()

        # Pop off headers
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        self.wfile.write("<html><head><title>bit.ly grinder</title></head>")
        self.wfile.write("<body><ul>")

        for bitly in get_results(db, 200):
            self.wfile.write('<li>%d - %s - <a href="%s">%s</a></li>' %
                             (bitly.status, bitly.base_url,
                              bitly.resolved_url,
                              bitly.resolved_url))

        self.wfile.write("</ul></body></html>")


def serve(port):
    """Simple HTTP server for browsing bit.ly grinder results"""
    Handler = BGHandler

    httpd = SocketServer.TCPServer(("", port), Handler)

    print "serving at port", port
    httpd.serve_forever()


def main():
    """Just launches the server"""
    serve(PORT)


if __name__ == "__main__":
    main()

__all__ = (serve)
