import urllib.request, urllib.error, urllib.parse
import json
import datetime
import csv
import time


def request_until_succeed(url, return_none_if_400=False):
    req = urllib.request.Request(url)
    success = False
    while success is False:
        try: 
            response = urllib.request.urlopen(req)
            if response.getcode() == 200:
                success = True
        except Exception as e:
            print(e)
            time.sleep(5)

            print("Error for URL %s: %s" % (url, datetime.datetime.now()))
            print("Retrying...")

            if return_none_if_400:
                if '400' in str(e):
                    return None;

    return response.read().decode()


def unicode_normalize(text):
    # Convert fancy quote chars and non-breaking spaces
    return text.translate({ 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22,
                            0xa0:0x20 }).encode('utf-8')


def get_comment_feed_data(status_id, access_token, num_comments):
    # Construct the URL string
    base = "https://graph.facebook.com/v2.6"
    node = "/%s/comments" % status_id 
    fields = "?fields=id,message,like_count,created_time,comments,from,attachment"
    parameters = "&order=chronological&limit=%s&access_token=%s" % \
            (num_comments, access_token)
    url = base + node + fields + parameters

    # retrieve data
    data = request_until_succeed(url, return_none_if_400=True)
    if data is None:
        return None
    else:   
        return json.loads(data)

def process_comment(comment, status_id, scrape_author_id, parent_id = ''):
    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.

    # Additionally, some items may not always exist,
    # so must check for existence first

    comment_id = comment['id']
    comment_message = '' if 'message' not in comment else \
            unicode_normalize(comment['message'])
    comment_author = unicode_normalize(comment['from']['name'])

    comment_author_id = "None"
    if "id" in comment["from"]:
        comment_author_id = unicode_normalize(comment['from']['id'])

    comment_likes = 0 if 'like_count' not in comment else \
            comment['like_count']

    if 'attachment' in comment:
        attach_tag = "[[%s]]" % comment['attachment']['type'].upper()
        comment_message = attach_tag if comment_message is '' else \
                (comment_message.decode("utf-8") + " " + \
                        attach_tag).encode("utf-8")

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    comment_published = datetime.datetime.strptime(
            comment['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
    comment_published = comment_published + datetime.timedelta(hours=-5) # EST
    comment_published = comment_published.strftime(
            '%Y-%m-%d %H:%M:%S') # best time format for spreadsheet programs

    # Return a tuple of all processed data

    if scrape_author_id:
        return (comment_id, status_id, parent_id, comment_message, 
                comment_author, comment_author_id, 
                comment_published, comment_likes)
    else:
        return (comment_id, status_id, parent_id, comment_message, 
                comment_author, 
                comment_published, comment_likes)

def scrape_comments(page_or_group_id, app_id, app_secret, 
        posts_input_file, output_filename, scrape_author_id):

    access_token = app_id + "|" + app_secret

    with open(output_filename, 'w') as file:
        w = csv.writer(file)
        if scrape_author_id:
            w.writerow(["comment_id", "status_id", "parent_id", "comment_message",
                "comment_author", "comment_author_id", 
                "comment_published", "comment_likes"])
        else:
            w.writerow(["comment_id", "status_id", "parent_id", "comment_message",
                "comment_author", 
                "comment_published", "comment_likes"])

        num_processed = 0   # keep a count on how many we've processed
        scrape_starttime = datetime.datetime.now()

        print("Scraping %s Comments From Posts: %s\n" % \
                (posts_input_file, scrape_starttime))

        with open(posts_input_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)

            for status in reader:
                has_next_page = True

                comments = get_comment_feed_data(status['status_id'], 
                        access_token, 100)

                while has_next_page and comments is not None:				
                    for comment in comments['data']:
                        w.writerow(process_comment(comment, 
                            status['status_id'], scrape_author_id))

                        if 'comments' in comment:
                            has_next_subpage = True

                            subcomments = get_comment_feed_data(
                                    comment['id'], access_token, 100)

                            while has_next_subpage:
                                for subcomment in subcomments['data']:
                                    w.writerow(process_comment( subcomment, 
                                            status['status_id'], 
                                            scrape_author_id,
                                            comment['id']))

                                    num_processed += 1
                                    if num_processed % 1000 == 0:
                                        print("%s Comments Processed: %s" % \
                                                (num_processed, 
                                                    datetime.datetime.now()))

                                if 'paging' in subcomments:
                                    if 'next' in subcomments['paging']:
                                        subcomments = json.loads(
                                                request_until_succeed(\
                                                    subcomments\
                                                        ['paging']['next'],
                                                    return_none_if_400=True))
                                    else:
                                        has_next_subpage = False
                                else:
                                    has_next_subpage = False

                        # output progress occasionally to make sure code is not
                        # stalling
                        num_processed += 1
                        if num_processed % 1000 == 0:
                            print("%s Comments Processed: %s" % \
                                    (num_processed, datetime.datetime.now()))

                    if 'paging' in comments:		
                        if 'next' in comments['paging']:
                            comments = json.loads(request_until_succeed(\
                                    comments['paging']['next'], 
                                    return_none_if_400=True))
                        else:
                            has_next_page = False
                    else:
                        has_next_page = False


        print("\nDone!\n%s Comments Processed in %s" % \
                (num_processed, datetime.datetime.now() - scrape_starttime))


def get_status_reactions(status_id, access_token):
    # See http://stackoverflow.com/a/37239851 for Reactions parameters
        # Reactions are only accessable at a single-post endpoint

    base = "https://graph.facebook.com/v2.6"
    node = "/%s" % status_id
    reactions = "/?fields=" \
            "reactions.type(LIKE).limit(0).summary(total_count).as(like)" \
            ",reactions.type(LOVE).limit(0).summary(total_count).as(love)" \
            ",reactions.type(WOW).limit(0).summary(total_count).as(wow)" \
            ",reactions.type(HAHA).limit(0).summary(total_count).as(haha)" \
            ",reactions.type(SAD).limit(0).summary(total_count).as(sad)" \
            ",reactions.type(ANGRY).limit(0).summary(total_count).as(angry)"
    parameters = "&access_token=%s" % access_token
    url = base + node + reactions + parameters

    # retrieve data
    data = json.loads(request_until_succeed(url))

    return data


def process_post(status, type_pg, access_token):
    # The status is now a Python dictionary, so for top-level items,
    # we can simply call the key.

    # Additionally, some items may not always exist,
    # so must check for existence first

    status_id = status['id']
    status_message = '' if 'message' not in list(status.keys()) else \
            unicode_normalize(status['message'])
    link_name = '' if 'name' not in list(status.keys()) else \
            unicode_normalize(status['name'])
    status_type = status['type']
    status_link = '' if 'link' not in list(status.keys()) else \
            unicode_normalize(status['link'])

    status_author = None
    if type_pg == "group":
        status_author = unicode_normalize(status['from']['name'])

    # Time needs special care since a) it's in UTC and
    # b) it's not easy to use in statistical programs.

    status_published = datetime.datetime.strptime(
            status['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
    status_published = status_published + \
            datetime.timedelta(hours=-5) # EST
    # best time format for spreadsheet programs
    status_published = status_published.strftime('%Y-%m-%d %H:%M:%S') 

    # Nested items require chaining dictionary keys.

    num_reactions = 0 if 'reactions' not in status else \
            status['reactions']['summary']['total_count']
    num_comments = 0 if 'comments' not in status else \
            status['comments']['summary']['total_count']
    num_shares = 0 if 'shares' not in status else \
            status['shares']['count']

    # Counts of each reaction separately; good for sentiment
    # Only check for reactions if past date of implementation:
    # http://newsroom.fb.com/news/2016/02/reactions-now-available-globally/

    reactions = get_status_reactions(status_id, access_token) if \
            status_published > '2016-02-24 00:00:00' else {}

    num_likes = 0 if 'like' not in reactions else \
            reactions['like']['summary']['total_count']

    # Special case: Set number of Likes to Number of reactions for pre-reaction
    # statuses

    num_likes = num_reactions if status_published < '2016-02-24 00:00:00' else \
            num_likes

    def get_num_total_reactions(reaction_type, reactions):
        if reaction_type not in reactions:
            return 0
        else:
            return reactions[reaction_type]['summary']['total_count']

    num_loves = get_num_total_reactions('love', reactions)
    num_wows = get_num_total_reactions('wow', reactions)
    num_hahas = get_num_total_reactions('haha', reactions)
    num_sads = get_num_total_reactions('sad', reactions)
    num_angrys = get_num_total_reactions('angry', reactions)

    # Return a tuple of all processed data.
    if type_pg == "group":
        # status_author only applies for groups
        return (status_id, status_message, status_author,
                link_name, status_type, status_link, status_published,
                num_reactions, num_comments, num_shares, num_likes, num_loves,
                num_wows, num_hahas, num_sads, num_angrys)
    elif type_pg == "page":
        return (status_id, status_message, 
                link_name, status_type, status_link, status_published,
                num_reactions, num_comments, num_shares, num_likes, num_loves,
                num_wows, num_hahas, num_sads, num_angrys)


def get_feed_data(page_or_group_id, type_pg, access_token, num_statuses):
    # Construct the URL string; see http://stackoverflow.com/a/37239851 for
    # Reactions parameters

    # the node field varies depending on whether we're scraping a page or a
    # group.
    posts_or_feed = str()

    base = "https://graph.facebook.com/v2.6"

    node = None
    fields = None
    if type_pg == "page":
        node = "/%s/posts" % page_or_group_id 
        fields = "/?fields=message,link,created_time,type,name,id," + \
                "comments.limit(0).summary(true),shares,reactions" + \
                ".limit(0).summary(true)"
    elif type_pg == "group":
        node = "/%s/feed" % page_or_group_id 
        fields = "/?fields=message,link,created_time,type,name,id," + \
                "comments.limit(0).summary(true),shares,reactions." + \
                "limit(0).summary(true),from"

    parameters = "&limit=%s&access_token=%s" % (num_statuses, access_token)
    url = base + node + fields + parameters

    # retrieve data
    data = json.loads(request_until_succeed(url))

    return data


def scrape_posts(page_or_group_id, type_pg, app_id, app_secret, output_filename):
    # Make sure that the type_pg argument is either "page" or "group
    is_page = type_pg == "page"
    is_group = type_pg == "group"

    assert (is_group or is_page), "type_pg must be either 'page' or 'group'"

    access_token = app_id + "|" + app_secret

    with open(output_filename, 'w') as file:
        w = csv.writer(file)
        if type_pg == "page":
            w.writerow(["status_id", "status_message", 
                "link_name", "status_type", "status_link", "status_published",
                "num_reactions", "num_comments", "num_shares", "num_likes",
                "num_loves", "num_wows", "num_hahas", "num_sads",
                "num_angrys"])
        elif type_pg == "group":
            # status_author only applies for groups
            w.writerow(["status_id", "status_message", "status_author", 
                "link_name", "status_type", "status_link", "status_published",
                "num_reactions", "num_comments", "num_shares", "num_likes",
                "num_loves", "num_wows", "num_hahas", "num_sads",
                "num_angrys"])

        has_next_page = True
        num_processed = 0   # keep a count on how many we've processed
        scrape_starttime = datetime.datetime.now()
        
        print("Scraping %s Facebook %s: %s\n" % (page_or_group_id, type_pg, scrape_starttime))

        statuses = get_feed_data(page_or_group_id, type_pg, access_token, 100)

        while has_next_page:
            for status in statuses['data']:

                # Ensure it is a status with the expected metadata
                if 'reactions' in status:
                    w.writerow(process_post(status, type_pg, access_token))

                # output progress occasionally to make sure code is not
                # stalling
                num_processed += 1
                if num_processed % 100 == 0:
                    print("%s Statuses Processed: %s" % \
                        (num_processed, datetime.datetime.now()))

            # if there is no next page, we're done.
            if 'paging' in list(statuses.keys()):
                
                if not 'next' in statuses['paging']:
                    has_next_page = False
                else:
                    statuses = json.loads(request_until_succeed(statuses['paging']['next']))
            else:
                has_next_page = False


        print("\nDone!\n%s Statuses Processed in %s" % \
                (num_processed, datetime.datetime.now() - scrape_starttime))
