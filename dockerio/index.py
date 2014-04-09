import json
import urllib
import urllib2

try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser


class DockerIndexRepoUpdated(HTMLParser):
    def __init__(self):
        self.check_is_update = False
        self.buf = ''
        self.waiting_date = False
        self.utc_date = None
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if self.utc_date:
            return
        if self.waiting_date and tag == 'span':
            dates = filter(lambda x: x[0] == 'utc-date', attrs)
            if len(dates) > 0:
                self.utc_date = dates[0][1]
        if tag != 'dt':
            return
        self.check_is_update = True

    def handle_data(self, data):
        if self.utc_date:
            return
        if not self.check_is_update:
            return
        if data == "Last updated":
            self.waiting_date = True

    def handle_endtag(self, tag):
        if self.utc_date:
            return
        self.buf = ''
        self.check_is_update = False

class DockerIndexRepoPage(HTMLParser):
    def __init__(self):
        self.buffering = False
        self.buf = ''
        self.dockerfile = ''
        HTMLParser.__init__(self)

    def handle_starttag(self, tag, attrs):
        if tag != 'code':
            return
        classes = filter(lambda x: x[0] == 'class', attrs)
        if len(classes) == 1 and classes[0][1] == 'dockerfile':
            self.buffering = True

    def handle_data(self, data):
        if not self.buffering:
            return
        self.buf += data

    def handle_endtag(self, tag):
        if not self.buffering:
            return

        self.dockerfile = self.buf
        self.buf = ''
        self.buffering = False

class DockerIndex(object):
    def search(self, term):
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'docker/0.7.5')]
        
        base_url = 'https://index.docker.io'
        path = '/v1/search'

        query = { 'q': term }
        uenc = urllib.urlencode(query)

        url = base_url + path + "?" + uenc
        print url
        resp = opener.open(url)
        return json.loads(resp.read())

    def get_dockerfile(self, repo):
        base_url = 'https://index.docker.io/u/'
        url = base_url + repo + '/'
        opener = urllib2.build_opener()
        try:
            resp = opener.open(url)
        except urllib2.HTTPError:
            return None

        parser = DockerIndexRepoPage()  #HTMLParser()        
        parser.feed(resp.read())

        return parser.dockerfile

    def get_last_updated(self, repo):
        base_url = 'https://index.docker.io/u/'
        url = base_url + repo + '/'
        opener = urllib2.build_opener()
        try:
            resp = opener.open(url)
        except urllib2.HTTPError:
            return None

        parser = DockerIndexRepoUpdated()
        parser.feed(resp.read())

        return parser.utc_date
