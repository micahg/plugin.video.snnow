import snnow
from settings import log
from adobe import AdobePass
import xbmc, xbmcplugin, xbmcgui, xbmcaddon, os, urllib, urlparse
import inputstreamhelper
__settings__ = xbmcaddon.Addon(id='plugin.video.snnow')
__language__ = __settings__.getLocalizedString


def getAuthCredentials():
    username = __settings__.getSetting("username")
    if len(username) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30000), __language__(30001))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    # get the password
    password = __settings__.getSetting("password")
    if len(password) == 0:
        dialog = xbmcgui.Dialog()
        dialog.ok(__language__(30002), __language__(30003))
        xbmcplugin.endOfDirectory(handle = int(sys.argv[1]),
                                  succeeded=False)
        return None

    mso = __settings__.getSetting("mso")

    return { 'u' : username, 'p' : password, 'm' : mso }


def createMainMenu():
    """
    Create the main menu
    """

    sn = snnow.SportsnetNow()

    channels = sn.getChannels()
    guide = sn.getGuideData()

    for channel in channels:
        chanId = str(channel['neulion_id'])
        desc = channel['name']
        if 'description' in channel:
            desc = channel['description']

        values = { 'menu' : 'channel', 'name' : desc,
                   'id' : channel['neulion_id'], 'abbr' : channel['id'] }

        title = values['name']
        showTitle = channel['name']

        if chanId in guide.keys():
            prog = guide[chanId]
            for key in prog.keys():
                values[key] = prog[key].encode('utf-8')

            if prog['tvshowtitle']:
                title += ' ([B]' + prog['tvshowtitle'] + '[/B]'
                if prog['title']:
                    title += ' - [I]' + prog['title'] + '[/I]'
                title += ')'

            showTitle = prog['tvshowtitle']

        live = xbmcgui.ListItem(title)

        labels = {"TVShowTitle" : showTitle,
                  "Studio" : desc}
        if 'title' in values:
            labels['Title'] = prog['title']
        if 'plot' in values:
            labels["Plot"] = prog['plot']
            labels['plotoutline'] = prog['plot']
        live.setInfo(type="Video", infoLabels=labels)
        if 'cast_image_url' in channel:
            live.setIconImage(channel['cast_image_url'])
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                    url=sys.argv[0] + "?" + urllib.urlencode(values),
                                    listitem=live,
                                    isFolder=True)

    # signal the end of the directory
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def playChannel(values):
    mso = __settings__.getSetting("mso")
    stream = getChannelStream(values['id'][0], values['abbr'][0], mso)
    token = stream['token']
    stream = stream['stream']
    headers = {
        ':authority': 'prod-lic2widevine.sd-ngp.net',
        ':method': 'POST',
        ':path': '/proxy',
        ':scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'en-CA%2Cen-GB%3Bq%3D0.9%2Cen-US%3Bq%3D0.8%2Cen%3Bq%3D0.7',
        'authorization': 'bearer {}'.format(token),
        'origin': 'https://now.sportsnet.ca',
        'referer': 'https://now.sportsnet.ca/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'content-type': '',
        'Accept-Charset': ''
    };

    header_str = '&'.join(["{}={}".format(k, v) for k, v in headers.items()])
    lic_srv = 'https://prod-lic2widevine.sd-ngp.net/proxy|{0}|R{{SSM}}|'.format(header_str)
    name = values['name'][0]

    inputstream_helper = inputstreamhelper.Helper('mpd', drm='widevine')
    if inputstream_helper.check_inputstream():
        li = xbmcgui.ListItem(name)

        labels = {}
        if 'tvshowtitle' in values:
            labels['TVShowTitle'] = values['tvshowtitle'][0]
        if 'name' in values:
            labels['Studio'] = values['name'][0]
        if 'title' in values:
            labels['Title'] = values['title'][0]
        if 'plotoutline' in values:
            labels["Plot"] = values['plot'][0]
        li.setInfo(type="Video", infoLabels=labels)

        # the following 4 lines borrowed from DAZN
        li.setMimeType('application/dash+xml')
        li.setProperty('inputstreamaddon', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'mpd')
        li.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
        li.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
        li.setProperty('inputstream.adaptive.license_key', lic_srv)

        p = xbmc.Player()
        p.play(stream, li)
    else:
        log("ERROR: inpustream helper check failed.", True);
        dialog.ok(__language__(30007), __language__(30008))


def getChannelStream(channelId, channelName, msoName):
    sn = snnow.SportsnetNow()
    stream = sn.getChannel(channelId, channelName, msoName)
    if not stream:
        # auth token may have expired - attempt re-auth first
        print('Auth token may have expired. Attempting re-auth.')
        creds = getAuthCredentials()
        if sn.authorize(creds['u'], creds['p'], creds['m']):
            return sn.getChannel(channelId, channelName, msoName)

    return stream

if len(sys.argv[2]) == 0:

    # create the data folder if it doesn't exist
    data_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    # log in
    if AdobePass.getAuthnToken() == None:
        progress = xbmcgui.DialogProgress()
        sn = snnow.SportsnetNow()
        creds = getAuthCredentials()
        if creds == None:
            xbmcplugin.endOfDirectory(int(sys.argv[1]))
            sys.exit(1)

        progress.create(__language__(30006), creds['m'])
        sn.checkMSOs()
        if not sn.authorize(creds['u'], creds['p'], creds['m']):
            dialog = xbmcgui.Dialog()
            dialog.ok(__language__(30004), __language__(30004))
            progress.close()
            sys.exit(1)
        progress.close()
    # show the main menu
    createMainMenu()
else:
    values = urlparse.parse_qs(sys.argv[2][1:])
    if values['menu'][0] == 'channel':
        playChannel(values)
