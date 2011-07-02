import sys, datetime, xmlrpclib, getopt

def main(argv):
    try:                                
        opts, args = getopt.getopt(argv, "hp:u:w:", ["help", "user=", "password=", "wordpress="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    
    wp_url = "http://localhosT/wordpress/xmlrpc.php"    
    wp_user = wp_passwd = None

    for opt in opts:
        if opt[0] == '-h':
            usage()
            sys.exit(0)
        if opt[0] == '-u':
            wp_user=opt[1]
        if opt[0] == '-p':
            wp_passwd=opt[1]
        if opt[0] == '-w':
            wp_url=opt[1]
            
    if wp_user == None:
        print "Need user argument!"
        usage()
        sys.exit(2)

    if wp_passwd == None:
        print "Need password argument!"
        usage()
        sys.exit(2)

    do_post(wp_url, wp_user, wp_passwd)

def usage ():
    print "ConvertPosts -u username -p password -w url"

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
