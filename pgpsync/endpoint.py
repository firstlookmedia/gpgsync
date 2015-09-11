class Endpoint(object):
    def __init__(self, fingerprint='', url='https://', keyserver='hkp://keys.gnupg.net', use_proxy=False, proxy_host='127.0.0.1', proxy_port='9050'):
        self.fingerprint = fingerprint
        self.url = url
        self.keyserver = keyserver
        self.use_proxy = use_proxy
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
