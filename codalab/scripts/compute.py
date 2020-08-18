#!/usr/bin/env python
#
#
import web

urls = ('/api/computation/(.+)', 'computation')


class computation:

    def GET(self, id):
        print("ID: %s" % id)

if __name__ == "__main__":
    app = web.application(urls, globals())
    app.internalerror = web.debugerror
    app.run()
