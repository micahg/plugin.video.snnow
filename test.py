#!/usr/bin/python
import sys, snnow, os
from cookies import Cookies
from optparse import OptionParser
from adobe import AdobePass

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
    if not stream:
        print "Unable to get stream"
        sys.exit(0)

    cookies = []
    streams = sn.parsePlaylist(stream, cookies)
    bitrates = [int(x) for x in streams.keys()]
    
    stream = None
    for bitrate in reversed(sorted(bitrates)):
        if stream == None:
            stream = streams[str(bitrate)]

    print stream

    if not options.ffplay == None:
        fstream = ""
        fstream += ' -cookies "'
        for cookie in cookies:
            fstream += cookie
        
        fstream += '" "' + stream.split('|')[0] + '"' 
        command = "ffplay " + fstream
        os.system(command)
else:
    for channel in  channels:
        prog = guide[str(channel['neulion_id'])]
        print str(channel['neulion_id']) + ') ' + channel['description'] + ' (' + \
              channel['id'] + ') - ' + str(prog)
