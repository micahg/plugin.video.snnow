import urllib, urllib2, re
from cookies import Cookies
from settings import log

class Rogers:
    """
    @class Rogers
    
    MSO class to handle authorization with the Rogers MSO
    """

    @staticmethod
    def getID():
        return 'Rogers'

    @staticmethod
    def authorize(streamProvider, username, password):
        """
        Perform authorization with Rogers

        @param streamProvider the stream provider object. Needs to handle the 
                              getAuthURI.
        @param username the username to authenticate with
        @param password the password to authenticate with
        """

        uri = streamProvider.getAuthURI('Rogers')

        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))#,
                                      #urllib2.HTTPHandler(debuglevel=1),
                                      #urllib2.HTTPSHandler(debuglevel=1))

        try:
            resp = opener.open(uri)
        except:
            log ("Unable get OAUTH location", True)
            return None
        Cookies.saveCookieJar(jar)

        html = resp.read()

        viewstate = re.search('<input.*__VIEWSTATE.*?value=\"(.*?)\".*?>', html, re.MULTILINE)
        if not viewstate:
            return None

        viewstategen = re.search('<input.*__VIEWSTATEGENERATOR.*?value=\"(.*?)\".*?>', html, re.MULTILINE)
        if not viewstategen:
            return None

        validation = re.search('<input.*__EVENTVALIDATION.*?value=\"(.*?)\".*?>', html, re.MULTILINE)
        if not validation:
            return None

        return Rogers.getOAuthToken(username, password, viewstate.group(1),
                                    viewstategen.group(1), validation.group(1),
                                    resp.url)


    @staticmethod
    def getOAuthToken(username, password, viewstate, viewstategen, validation, url):
        """
        Perform OAuth
        @param username the username
        @param password the password
        @param viewstate the viewstate (form data)
        @param validation the validation (form data)
        @param url the OAuth URL
        """
        jar = Cookies.getCookieJar()
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar))

        values = {'__VIEWSTATE' : viewstate,
                  '__VIEWSTATEGENERATOR' : viewstategen,
                  '__EVENTVALIDATION' : validation,
                  'UserName' : username,
                  'UserPassword' : password,
                  'Login' : 'Sign in' }

        try:
            resp = opener.open(url, urllib.urlencode(values))
        except urllib2.URLError, e:
            log (e.args, True)
        Cookies.saveCookieJar(jar)

        return True