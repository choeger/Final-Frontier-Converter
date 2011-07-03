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

import sys, datetime, xmlrpclib, getopt, re
import mysql.connector as db
import httplib, base64

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

ereg_replacements = {
    "\\[#=([^]]*)\\]" : "<a name=\"\\1\"></a>",
    "===([^=]+)===" : "<h3>\\1</h3>",
    "==([^=]+)==" : "<h2>\\1</h2>",
    "\\[\\[([^]^ ]+) ([^]]*)\\]\\]" : "<a href=\"\\1\">\\2</a>",
    "\\[\\[([^]^ ]+)\\]\\]" : "<a href=\"\\1\">\\1</a>",
    #"\\[img=([^,]+),([^,]*),([^,]*),([^,]*),([^]]*)\\]" : "<img src=\\1 width=\\2 height=\\3 align=\\4 hspace=5 vspace=5 title=\"\\5\" alt=\"\\5\">"
    "\\[img=([^,]+),([^,]*),([^,]*),([^,]*),([^]]*)\\]" : "[caption align=\"align\\4\" width=\"\\2\" caption=\"\\5\"]<img src=\"\\1\" alt=\"\\5\" title=\"\\5\" width=\"\\2\" height=\"\\3\" class=\"size-full\" /></a>[/caption]"
}

str_replacements = {
    "width=," : "width=",
    "height=," : "height=",
    "align=," : "align=",
    "alt=," : "alt=",
    "width= " : " ",
    "height= " : " ",
    "align= " : " "
}

def replaceTags(images, input):
    text = input
    for regex, replace in ereg_replacements.iteritems():
        text = re.sub(regex, replace, text)

    for search, replace in str_replacements.iteritems():
        text = text.replace(search, replace)

    for img, url in images.iteritems():
        text = text.replace('src="' + img + '"', 'src="' + url + '"')

    return text
        
def nl2br(input):
    return input.replace("\n", "<br />\n")

def encodeContent(images, content, abstract) :
    return replaceTags(images, nl2br(abstract)) + "\n<!--more-->\n" + replaceTags(images, nl2br(content))

def convertImages(input):
    images = []
    conn = httplib.HTTPConnection("www.final-frontier.ch")
    
    for img in re.findall("\\[img=([^,]+),([^,]*),([^,]*),([^,]*),([^]]*)\\]", input):
        loc = "/images/" + img[0]
        print "GET " + loc
        conn.request("GET", loc)
        res = conn.getresponse()
        if res.status == 200:
            data = res.read()
            yield (img[0], xmlrpclib.Binary(data))
        else:
          print str(res.status)

def convertPosts() :
    wp_blogid=0
    server = xmlrpclib.ServerProxy(options['wp_url'])
    conn = db.connect(user=options['my_user'], password=options['my_password'], db=options['my_db'])
    cursor = conn.cursor()

    image_map = { }

    def uploadImage(name, data):
        media_object = {'name' : name, 'bits' : data, 'type' : 'image/gif' }
        up = server.wp.uploadFile(wp_blogid, options['wp_user'], options['wp_password'], media_object)
        image_map[name] = up['url']
 
    # convert categories
    categories = {}
    cursor.execute("SELECT * FROM rubrik WHERE webseite_id=2")
    for row in cursor:
        print "Found category: " + row[1]
        categories[row[0]] = row[1]
        cat_data = {'name': row[1], 'slug' : '', 'description': '', 'parent_id' : 0}
        server.wp.newCategory(wp_blogid, options['wp_user'], options['wp_password'], cat_data)

    # convert blog posts
    cursor.execute("SELECT * FROM inhalt WHERE webseite_id=2 AND pagetyp_id=3")   
    rows = cursor.fetchall()
    for row in rows:
        image_map = { }
        print "Converting Blog post: " + row[1]
        
        cat = [categories[row[5]]]        
        status_draft = 0
        status_published = 1

        old_id = row[0]
        title = row[1]
        for name, data in convertImages(row[13]):
            uploadImage(name, data)

        for name, data in convertImages(row[11]):
            uploadImage(name, data)
 
        content = encodeContent(image_map, row[13], row[11])
        date_created = row[7]
        tags = row[12]
        print "Keywords: " + tags

        data = {'title': title, 'description': content, 'dateCreated': date_created, 'pubDate' : date_created, 'categories': cat, 'mt_keywords': tags, 'wp_slug' : row[2]}
        
        post_id = server.metaWeblog.newPost(wp_blogid, options['wp_user'], options['wp_password'], data, status_published)
        #convert comments
        cursor.execute("SELECT * FROM kommentar WHERE bezug_id=" + str(old_id))
        comments=cursor.fetchall()
        comment_nr = 0
        for comment in comments:
            comment_nr += 1
            print "[" + str(comment_nr) + "/" + str(len(comments)) + "] Adding comment " + str(comment[0]) + " for post " + str(comment[1]) + " from " + comment[2] 
            author = comment[2]
            url = comment[3]
            content = comment[4]
            date = comment[5]
            comment_data = {'comment_parent' : 0, 'author' : author, 'author_url' : url, 'content' : content, 'date_created_gmt' : date}
            comment_id = server.wp.newComment(wp_blogid, options['wp_user'], options['wp_password'], post_id, comment_data)
            server.wp.editComment(wp_blogid, options['wp_user'], options['wp_password'], comment_id, comment_data)
        print "Done."

if __name__ == "__main__":
    main(sys.argv[1:])
