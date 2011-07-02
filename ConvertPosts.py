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

def main(argv):
    try:                                
        opts, args = getopt.getopt(argv, "h", ["help", "wp_user=", "wp_password=", "wp_url=", "my_user=", "my_password="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    # default and required options
    options = { 'wp_url' : "http://localhost/wordpress/xmlrpc.php",
                'wp_user' : None, 'wp_password' : None,
                'my_user' : None, 'my_password' : None,
                }
    
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

    do_post(options['wp_url'], options['wp_user'], options['wp_password'])

def usage ():
    print "ConvertPosts --wp_user=username --wp_password=password --wp_url=url"

def do_post(wp_url, wp_user, wp_pass):
    wp_blogid=''
    status_draft = 0
    status_published = 1

    server = xmlrpclib.ServerProxy(wp_url)

    title = "Title with spaces III"
    content = "<h1>Body</h1> with lots of <b>content</b>"
    date_created = xmlrpclib.DateTime(datetime.datetime.strptime("1981-10-20 21:08", "%Y-%m-%d %H:%M"))
    categories = ["somecategory"]
    tags = ["sometag", "othertag"]
    data = {'title': title, 'description': content, 'dateCreated': date_created, 'pubDate' : date_created, 'categories': categories, 'mt_keywords': tags}

    post_id = server.metaWeblog.newPost(wp_blogid, wp_user, wp_pass, data, status_published)


if __name__ == "__main__":
    main(sys.argv[1:])
