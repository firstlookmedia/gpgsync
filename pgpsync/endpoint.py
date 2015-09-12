import uuid

class Endpoint(object):
    def __init__(self):
        # each endpoint needs a unique id
        self.id = uuid.uuid4()

        # set defaults
        self.update(fingerprint='', url='https://', keyserver='hkp://keys.gnupg.net',
            use_proxy=False, proxy_host='127.0.0.1', proxy_port='9050')

    def update(self, fingerprint=None, url=None, keyserver=None, use_proxy=None, proxy_host=None, proxy_port=None, last_checked=None):
        if fingerprint != None:
            self.fingerprint = str(fingerprint)
        if url != None:
            self.url = str(url)
        if keyserver != None:
            self.keyserver = str(keyserver)
        if use_proxy != None:
            self.use_proxy = bool(use_proxy)
        if proxy_host != None:
            self.proxy_host = str(proxy_host)
        if proxy_port != None:
            self.proxy_port = str(proxy_port)
        if last_checked != None:
            self.last_checked = False
