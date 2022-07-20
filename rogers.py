from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
import urllib.request, urllib.parse, urllib.error, urllib.request, urllib.error, urllib.parse, re
from cookies import Cookies

class Rogers(object):
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
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))#,
                                      #urllib2.HTTPHandler(debuglevel=1),
                                      #urllib2.HTTPSHandler(debuglevel=1))

        try:
            resp = opener.open(uri)
        except:
            print("Unable get OAUTH location")
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
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

        values = {'__VIEWSTATE' : viewstate,
                  '__VIEWSTATEGENERATOR' : viewstategen,
                  '__EVENTVALIDATION' : validation,
                  'UserName' : username,
                  'UserPassword' : password,
                  'Login' : 'Sign in' }

        try:
            resp = opener.open(url, urllib.parse.urlencode(values))
        except urllib.error.URLError as e:
            print(e.args)
        Cookies.saveCookieJar(jar)

        return True