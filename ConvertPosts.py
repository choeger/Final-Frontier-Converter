#!/usr/bin/env python
# -*- coding: utf-8 -*-

# final-frontier.ch -> wordpress conversion tools
# <choeger@umpa-net.de>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA

import sys, datetime, xmlrpclib, getopt 
import mysql.connector as db

# default and required options
options = { 'wp_url' : "http://localhost/wordpress/xmlrpc.php",
            'wp_user' : None, 'wp_password' : None,
            'my_user' : None, 'my_password' : None,
            'my_db' : 'final_frontier'
            }

def main(argv):
    try:                                
        opts, args = getopt.getopt(argv, "h", ["help", "wp_user=", "wp_password=", "wp_url=", "my_user=", "my_password="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    for opt in opts:
        if opt[0] == '-h' or opt[0] == '--help':
            usage()
            sys.exit(0)
        else: 
            options[opt[0][2:]] = opt[1]

    for k,v in options.iteritems():
        if v == None:
            print "Option " + k + " is required!"
            sys.exit(2)

    convertPosts()

def usage ():
    print "ConvertPosts --wp_user=username --wp_password=password --wp_url=url"

def encodeContent(content, abstract) :
    return abstract + "\n<!--more-->\n" + content

def convertPosts() :
    wp_blogid=''
    server = xmlrpclib.ServerProxy(options['wp_url'])
    conn = db.connect(user=options['my_user'], password=options['my_password'], db=options['my_db'])
    cursor = conn.cursor()

    categories = {}
    cursor.execute("SELECT * FROM rubrik WHERE webseite_id=2")
    for row in cursor:
        print "Found category: " + row[1]
        categories[row[0]] = row[1]
        cat_data = {'name': row[1], 'slug' : '', 'description': '', 'parent_id' : 0}
        server.wp.newCategory(wp_blogid, options['wp_user'], options['wp_password'], cat_data)

    cursor.execute("SELECT * FROM inhalt WHERE webseite_id=2 AND pagetyp_id=3")
    for row in cursor:
        print "Converting Blog post: " + row[1]
        
        cat = [categories[row[5]]]        
        status_draft = 0
        status_published = 1

        title = row[1]
        content = encodeContent(row[13], row[11])
        date_created = row[7]
        tags = row[12]
        print "Keywords: " + tags

        data = {'title': title, 'description': content, 'dateCreated': date_created, 'pubDate' : date_created, 'categories': cat, 'mt_keywords': tags }
        
        post_id = server.metaWeblog.newPost(wp_blogid, options['wp_user'], options['wp_password'], data, status_published)
        print "Done."

if __name__ == "__main__":
    main(sys.argv[1:])
