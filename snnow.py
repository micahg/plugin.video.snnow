import urllib, urllib2, random, time, datetime, json, xml.dom.minidom, re
from adobe import AdobePass
from msofactory import MSOFactory
from cookies import Cookies
from settings import Settings, log
from urlparse import urlparse


class SportsnetNow:

    def __init__(self):
        """
        Initialize the sportsnet class
        """
        self.CONFIG_URI = 'https://static.rogersdigitalmedia.com/sportsnet-mobile-app/config.json'
        self.CHANNELS_URI = 'https://now.sportsnet.ca/service/channels?format=json'
        self.AUTHORIZED_MSO_URI = 'https://sp.auth.adobe.com/adobe-services/1.0/config/SportsnetNow'
        self.PUBLISH_POINT = 'https://now.sportsnet.ca/service/publishpoint?'
        self.USER_AGENT = 'Mozilla/5.0 (iPad; CPU OS 8_3 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Mobile/12F69 ipad sn now 4.0912'
        #self.USER_AGENT = 'Mozilla/5.0 (Linux; Android 6.0.1; ONE A2005 Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/56.0.2924.87 Mobile Safari/537.36 sportsnet 2.5.1'
        self.EPG_PREFIX = 'http://smb.cdnak.nyc.neulion.com/u/smb/sportsnetnow/configs/epg/'

    @staticmethod
    def instance():
        return SportsnetNow()


    def name(self):
        return "Sportsnet Now"


    def getCategories(self):
        return [ 'live' ]


    def getRequestorID(self):
        return "SportsnetNowCA"


    def getSignedRequestorID(self):
        return 'uwA5R37PTXqe6tnY3r2XiViL0C/COzz0eEMGEKtjoMbXV4RWw59fuP12jMF2c5rh9tJYe1RTkp6oZcqepsmbwtDBpUP+w158M54S+nmvMzOMN4qVf2PAAq1ZmIWUTxnommPs+jYbEnkujoAbUm4vnrzIARv58twwtHORYhqF/aUTpHRgeNVVYF8Lc9+zFYidbRNN8Wipr1QcePT45B463m1h4hd8dS9cMHfMge+V5Bsxh/0MXy+06iDABLllbifWQ0iGsMwuMNHORRYIpf9bzGaWYbC7qqrd9z5Q1dmNsrpYKqVDPHYqxFN7YXc3wLhWjuam7v5RB5ogL3IlrV1AQyLX2in1jSsx8qdwbTJjT/gfimIlaFrCPfWJG7nSRKxa1yGwtY2R9WTXLPlxMNNtFq+lown01TPpeUhxxkeXdl70bReZcb/5Eq/YRuAbdt6FgvvPQUlrz9vRsVtiEx8+700cNd80Yehre553Vt7xoP1qmaLV/8K+/jvZASQ5D+gnkwifZ92f6YIfH7kzORN1pgmeJYxCbKw/pE1Fncp1NuEGoG8cYtxA3mb053QS4yFxepe3yq6gcSlwlQfxOl2JpXO5Ye/2OK8nqc3Z1Pdx343F1W7G4TdN0CORD8C4ELo0m6zPNFOwhHF21ErB2M4xju8/996GfSIqtciK0WmDDrk='


    def getDeviceID(self):
        #return 64 hex characters
        settings = Settings.instance().get(self.getRequestorID())
        dev_id = ''
        if not settings:
            dev_id = ''
        elif 'DEV_ID' in settings.keys():
            dev_id = settings['DEV_ID']

        if not dev_id:
            dev_id = ''.join(random.choice('0123456789abcdef') for _ in range(16))
            Settings.instance().store(self.getRequestorID(), 'DEV_ID', dev_id)

        return dev_id


    def getAuthURI(self, mso):
        """
        Get the Sportsnet Now OAuth URI. This is going to be called by the MSO
        class to get the authorization URI for hte specific provider

        @param mso the multi-system operator (eg: Rogers)
        """
        return 'https://sp.auth.adobe.com/adobe-services/authenticate/saml?domain_name=adobe.com&noflash=true&no_iframe=true&mso_id={}&requestor_id=SportsnetNowCA&redirect_url=adobepass%3A%2F%2Fandroid.app&client_type=android&client_version=1.9.2'.format(mso)
 


    def checkMSOs(self):
        """
        Check the available MSOs. We don't actually use anything from this
        request other than the cookies returned.
        """
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.AUTHORIZED_MSO_URI)
        except:
            print "Unable get OAUTH location"
            return None
        Cookies.saveCookieJar(jar)

        mso_xml = resp.read()
        return None


    def getServerTime(self):
        """
        Convert the local time to GMT-5, the timezone in which the guide data is
        stored.
        """
        loc_time = datetime.datetime.fromtimestamp(time.mktime(time.localtime()))
        gmt_time = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
        delta = gmt_time - loc_time
        delta = datetime.timedelta(seconds = delta.seconds - 18000)
        return datetime.datetime.now() + delta


    def getGuideData(self):
        """
        Get the guid data for the channels right now.
        """
        now = self.getServerTime()
        url = self.EPG_PREFIX + now.strftime("%Y/%m/%d.xml")

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(url)
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        guide_xml = resp.read()
        guide = {}
        dom = xml.dom.minidom.parseString(guide_xml)
        channels_node = dom.getElementsByTagName('channelEPG')[0]
        for channel_node in channels_node.getElementsByTagName('EPG'):
            cid = channel_node.attributes['channelId'].value
            curr_item = None
            for item in channel_node.getElementsByTagName('item'):
                time_str = item.attributes['sl'].value.split('.')[0]
                item_time = time.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
                item_time = datetime.datetime.fromtimestamp(time.mktime(item_time))

                if item_time > now:
                    break
                curr_item = item

            if curr_item:
                show = {}
                try:
                    title = curr_item.attributes['t']
                except:
                    title = curr_item.attributes['e']
                episode = curr_item.attributes['e']
                
                try:
                    description = curr_item.attibutes['ed']
                    show['plot'] = description.value.encode('utf-8').strip().decode('utf-8')
                except:
                    show['plot'] = 'No description found'
                
                show['tvshowtitle'] = title.value.encode('utf-8').strip().decode('utf-8')
                show['title'] = episode.value.encode('utf-8').strip().decode('utf-8')
                
                guide[cid] = show

        return guide


    def getChannels(self):
        settings = Settings.instance().get(self.getRequestorID())
        if settings and 'CHANNELS' in settings.keys():
            return settings['CHANNELS']

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.CONFIG_URI)
        except urllib2.URLError, e:
            print e.args
            return None
        Cookies.saveCookieJar(jar)

        config_js = resp.read()
        config = json.loads(config_js)
        channels = config['adobepass_details']['channels']
        Settings.instance().store(self.getRequestorID(), 'CHANNELS', channels)
        return channels


    def authorize(self, username, password, msoName='Rogers'):
        """
        Authorize with the MSO credentials
        @param username the username
        @param password the password
        @param the MSO (eg: Rogers)
        """

        # Get the MSO class from the 
        mso = MSOFactory.getMSO(msoName)
        if mso == None:
            print "Invalid MSO"
            return None

        # Authorize with the MSO
        if not mso.authorize(self, username, password):
            print "Failed to authorize with MSO"
            return False

        channels = self.getChannels()
        if mso.getID() == 'Sportsnet':
            return True

        if not AdobePass.sessionDevice(self):
            print "Session device failed."
            return False

        result = AdobePass.preAuthorize(self, channels)
        if not result:
            print "Preauthorize failed."
            return False

        return True


    def logout(self):
        # delete token from settings
        return None


    def getChannel(self, id, name, msoName):
        """
        Get the channel stream address.
        @param id The channle id
        @param name The channel name
        @param the MSO name (eg: Rogers)
        """
        mso = MSOFactory.getMSO(msoName)
        if mso == None:
            print "Invalid MSO"
            return None

        mso_id = mso.getID()
        token = None
        if mso_id != 'Sportsnet':
            ap = AdobePass()
            if not ap.authorizeDevice(self, mso_id, name):
                print "Authorize device failed"
                return None

            token = AdobePass.deviceShortAuthorize(self, msoName)
        return self.getPublishPoint(id, name, token)


    def getPublishPoint(self, id, name, token):
        """
        Get the stream address. Do not call directly.
        @param name the channel name
        @param token the token to authorize the stream
        """
        values = { 'format' : 'json',
                   'id' : id,
                   'type' : 'channel',
                   'nt' : '1',
                   'drmtoken': 'true'}

        if token:
            values['aprid'] = name
            values['aptoken'] = token

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))
        #opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(self.PUBLISH_POINT, urllib.urlencode(values))
        except urllib2.HTTPError as err:
            log("getPublishPoint {0}: '{1}'".format(err.code, err.reason), True)
            resp = err.read()
            log("getPublishPoint returns '{0}'".format(resp))
            return None
        except urllib2.URLError as err:
            log("getPublishPoint: '{0}'".format(err.reason), True)
            return None

        Cookies.saveCookieJar(jar)

        js_str = resp.read()

        result = json.loads(js_str)
        return { 'stream': result['path'], 'token': result['drmToken'] }


    def parsePlaylist(self, url, raw_cookies = None):
        """
        Parse the playlist and split it by bitrate.
        """
        streams = {}
        opener = urllib2.build_opener()
        opener.addheaders = [('User-Agent', urllib.quote(self.USER_AGENT))]

        try:
            resp = opener.open(url)
        except urllib2.URLError, e:
            print e.args
            return streams
        except urllib2.HTTPError, e:
            print e.getcode()
            return streams

        cookie_str = ''
        cookies = []
        for header in resp.info().headers:
            if header[:10] == 'Set-Cookie':
                cookie = header[12:]
                cookie_str += urllib.quote(cookie.strip() + '\n' )
                if raw_cookies != None:
                    raw_cookies.append(cookie)
                cookies.append(cookie.strip())

        m3u8 = resp.read();

        url = urlparse(url)
        prefix = url.scheme + "://" + url.netloc + url.path[:url.path.rfind('/')+1]
        lines = m3u8.split('\n')

        bandwidth = ""
        for line in lines:
            if line == "#EXTM3U":
                continue
            if line[:17] == '#EXT-X-STREAM-INF':
                bandwidth = re.search(".*,?BANDWIDTH\=(.*?),", line)
                if bandwidth:
                    bandwidth = bandwidth.group(1)
                else:
                    print "Unable to parse bandwidth"
            elif line[-5:] == ".m3u8":

                stream = prefix + line + "|User-Agent={0}".format(urllib.quote(self.USER_AGENT))
                """cookie_num = 0
                for cookie in cookies:
                    stream += "&Cookie{0}={1}".format(str(cookie_num), urllib.quote(cookie))
                    cookie_num += 1
                streams[bandwidth] = stream
                """
                stream = prefix + line + "|User-Agent={0}&Cookies={1}"
                stream = stream.format(urllib.quote(self.USER_AGENT),cookie_str)
                streams[bandwidth] = stream

        return streams