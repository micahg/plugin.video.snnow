#!/usr/bin/python
import requests, logging


try: # for Python 3
    from http.client import HTTPConnection
except ImportError:
    from httplib import HTTPConnection
HTTPConnection.debuglevel = 1

logging.basicConfig() # you need to initialize logging, otherwise you will not see anything from requests
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

import sys, snnow, os
from cookies import Cookies
from optparse import OptionParser
from adobe import AdobePass


def playChannel(mso, token):

    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-CA,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'bearer {}'.format(token),
        'origin': 'https://now.sportsnet.ca',
        'referer': 'https://now.sportsnet.ca/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        '%3Aauthority': 'prod-lic2widevine.sd-ngp.net',
        '%3Amethod': 'POST',
        '%3Apath': '/proxy',
        '%3Ascheme': 'https',
    };

    r = requests.post('https://prod-lic2widevine.sd-ngp.net/proxy', data='', headers=headers)

    print 'Status code is {}'.format(str(r.status_code))

    return


# parse the options
parser = OptionParser()
parser.add_option('-u', '--user', type='string', dest='user',
                  help="Username for authentication")
parser.add_option('-p', '--password', type='string', dest='password',
                  help="Password for authentication")
parser.add_option('-i', '--id', type='int', dest='id',
                  help="Channel ID")
parser.add_option('-m', '--mso', type='string', dest='mso', default='Rogers',
                  help="Multi-system operator (eg: Rogers)")
parser.add_option('-f', '--ffplay', action="store_true", dest='ffplay',
                  help='Choose a stream and get it ready for ffplay')

(options, args) = parser.parse_args()

sn = snnow.SportsnetNow()
channels = sn.getChannels()
guide = sn.getGuideData()
abbr = None

if options.user != None and options.password != None:
    if not sn.authorize(options.user, options.password, options.mso):
        sys.exit(1)
    print "Authorization Complete."

for channel in  channels:
    if options.id:
        if options.id == channel['neulion_id']:
            abbr = channel['id']

if abbr:
    # ensure an MSO
    if options.mso == None:
        print "No MSO specified"
        sys.exit(1)

    if AdobePass.getAuthnToken() == None:
        print "Not logged in..."
        sys.exit(1)

    stream = sn.getChannel(options.id, abbr, options.mso)
    token = stream['token']
    stream = stream['stream']

    #print 'Stream is {}\n\nToken is {}'.format(stream, token)
    playChannel(stream, token)

else:
    for channel in  channels:
        prog = guide[str(channel['neulion_id'])]
        desc = channel['description'] if 'description' in channel else ".*???*."
        chan_id = channel['id']

        print str(channel['neulion_id']) + ') ' + desc + ' (' + chan_id + ') - ' + str(prog)
