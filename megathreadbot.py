#!/usr/bin/env python
# -*- coding: utf-8 -*-

# TO DO:
# MUST STRIP () FROM URLS, AS THEY FUCK UP REDDIT URL FORMATTING
# GIVEN THIS WOULD KILL A URL, THEY SHOULD NOT BE LISTED

import os
import re
import praw
import time
import logging
from urlparse import urlparse

#  logging.basicConfig(level=logging.DEBUG)
try:
	r = praw.Reddit('megathreadbot',
      		         user_agent='finds links for r/politics for our megathreads')
	print 'Authentication Successful'
	print r.user.me()

except Exception as e:
    print 'Authentication Failed!'
    print str(e)
    exit()

subreddit = r.subreddit('politics')

urls = {}     #  Tracks active megathreads and urls associated with them
payload = {}  #  This is the data submitted to the actual text field
used = []     #  This determines what megathreads were updated on last scan
              #  In event of 2 megathreads, perhaps only one needs an update, we then
              #  Add updated info at end of script

paths = []    #  Paths are for actual checking if a link already exists in op
              #  Slightly redundant with urls{}, but i dont want to mess things up atm
              #  Full urls are needed in some circumstances in this script
              #  At later date we prob merge this with urls{}


def scan_unmod():

    used = []  # We want this empty for every new iteration
    for submission in subreddit.new(limit=100):
        if not submission.mod_reports:
            continue
        if not re.search(r'megathread\w{6}', submission.mod_reports[0][0]):
            #  idiot proofing
            continue
        else:
            link_id = submission.mod_reports[0][0].split('megathread')[1]
            print submission.id.encode('utf-8')
            if link_id in used:
                pass
            else:
                used.append(link_id)

            if link_id not in urls:
                #  If there are any urls in selfpost we load them

                regex = re.compile(ur'\]\((.*)\)')
                megathread = r.submission(id=link_id)

                #  Creates an entry that looks like {'link1': [url1, url2, url3]}
                #  Allows us to have multiple megathreads at once, i.e.:
                #  {'mega1': [url1, url2, url3]}
                #  {'megaTwo': [url1, url2, url3]}
                urls[link_id] = re.findall(regex, megathread.selftext)

                if 'SUBMISSION | DOMAIN' not in megathread.selftext:
                    payload[link_id] = ('\n\n---\n\n##Submissions that may '
                                        'interest you'
                                        '\n\nSUBMISSION | DOMAIN'
                                        '\n---|----')
                else:
                    payload[link_id] = ''


            long_url = urlparse(submission.url)
            url_path = long_url.path
            if url_path not in paths:
                #  Meets all the conditions to be submitted to OP

                sub_title = submission.title.encode('utf-8', 'replace')
                #  '|' character fucks up reddit formatting:
                sub_title = sub_title.replace('|', '-')
                sub_url = submission.url.encode('utf-8', 'replace')
                sub_domain = submission.domain.encode('utf-8', 'replace')
                if submission.author != None:
                    author = submission.author.name.encode('utf-8', 'replace')
                else:
                    author = 'Deleted'
                    author = author.encode('utf-8')

                payload[link_id] += '\n[{}]({}) | {}'.format(
                    sub_title,
	                sub_url,
                    sub_domain)

                urls[link_id].append(submission.url)
                paths.append(url_path)

                message = ('Hello `{}`, thank you for participating on '
                           'r/politics. The topic of your submission is '
                           'currently being discussed at length in our '
                           '[megathread.](http://redd.it/{})  Given the '
                           'large scale nature of this news, we are '
                           'temporarily removing all submissions concerning '
                           'this topic so that the community has one easy '
                           'to find place for discussion and news updates. '
                           'That said, **your submission has been selected** '
                           'to be featured in our megathread OP! We thank you '
                           'for your contribution to this subreddit, it '
                           'is very much appreciated.\n\nIf you have any '
                           'questions about this removal, please feel '
                           'free to [message the moderators.]'
                           '(https://www.reddit.com/message/compose?to='
                           '/r/politics&subject=Question regarding removal'
                           ' due to megathread by /u/{}&message=I have a '
                           'question regarding the removal of this '
                           '[submission.]({}?context=10000\))').format(
                    author, link_id,
                    author, submission.url)

                submission.reply(message).mod.distinguish(how='yes')
                submission.mod.remove()
		permalink = submission.permalink.encode('utf-8', 'replace')
                print 'SELECTED {}'.format(permalink)

            else:
                #  Otherwise good submission, but already in OP
                if submission.author != None:
                    author = submission.author.name.encode('utf-8')
                else:
                    author = '~~Deleted~~'
                    author = author.encode('utf-8')
                message = ('Hello `{}`, thank you for participating on '
                           'r/politics. The topic of your submission is '
                           'currently being discussed at length in our '
                           '[megathread.](http://redd.it/{})  Given the '
                           'large scale nature of this news, We are '
                           'temporarily removing all submissions concerning '
                           'this topic so that the community has one easy '
                           'to find place for discussion and news updates. '
                           'Thank you for your understanding.\n\nIf you have '
                           'any questions about this removal, please feel '
                           'free to [message the moderators.]'
                           '(https://www.reddit.com/message/compose?to='
                           '/r/politics&subject=Question regarding removal'
                           ' due to megathread by /u/{}&message=I have a '
                           'question regarding the removal of this '
                           '[submission.]({}?context=10000\))').format(
                    author, link_id,
                    author, submission.url)
                    # this is where the author error is
                    # url is in path, but the author is deleted, and thus
                    # undefined

                submission.reply(message).mod.distinguish(how='yes')
                submission.mod.remove()
		permalink = submission.permalink.encode('utf-8', 'replace')
                print 'Removed {} - (Already in OP)'.format(
                    permalink)

    for link_id in used:
        try:
            megathread = r.submission(id=link_id)
            selftext = megathread.selftext.encode('utf-8', 'replace')
            megathread.edit(selftext + payload[link_id])
            payload[link_id] = ''  #  Erase after completion
        except Exception as e:
            print str(e)

def run():
    while True:
        try:
      	    start = time.time()
      	    page = r.subreddit('politicsmod').wiki['seconds']
      	    seconds = page.content_md.replace(' ','')
      	    seconds = seconds.split('=')[1]
      	    seconds = int(seconds)
            print '-> Begin Scan:'
            scan_unmod()
            print '-> Scan Complete...'
            finish = time.time() - start
            print '-> Script time: {}'.format(finish)
            time.sleep(seconds)
        except Exception as e:
            print 'outside scan function'
            print str(e)
            time.sleep(30)

if __name__ == "__main__":

    run()
