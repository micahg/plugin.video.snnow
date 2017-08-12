#!/usr/bin/python
import sys, snnow, os
from cookies import Cookies
from optparse import OptionParser
from adobe import AdobePass
from wildvine import Wildvine

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
    if AdobePass.getAuthnToken() == None:
        print "Not logged in..."
        sys.exit(1)

    stream = sn.getChannel(options.id, abbr, options.mso)
    token = stream['token']
    stream = stream['stream']

    print 'Stream is {}\nToken is {}'.format(stream, token)
    
    Wildvine.first(token)
else:
    for channel in  channels:
        prog = guide[str(channel['neulion_id'])]
        print str(channel['neulion_id']) + ') ' + channel['description'] + ' (' + \
              channel['id'] + ') - ' + str(prog)
