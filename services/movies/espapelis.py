"""Services for hentaistube controller"""
# Retic
from retic import App as app

# Requests
import requests

# bs4
from bs4 import BeautifulSoup
from retic.services.responses import success_response

# Time
from time import sleep

# services
import services.general.wordpress as wordpress

# Constants
ESPAPELIS_URL = app.config.get('ESPAPELIS_URL')
ESPAPELIS_LOGIN = app.config.get('ESPAPELIS_LOGIN')
ESPAPELIS_ADMIN = app.config.get('ESPAPELIS_ADMIN')
ESPAPELIS_USERNAME = app.config.get('ESPAPELIS_USERNAME')
ESPAPELIS_PASSWORD = app.config.get('ESPAPELIS_PASSWORD')


def scrapper_espapelis_movies(_page=1):
    """Variables"""
    _items = []
    _url = '{0}/wp-admin/admin-ajax.php'.format(ESPAPELIS_URL)
    _params = {
        u'range': _page,
        u'action': "action_pelisplushd"
    }

    _session = wordpress.login(
        ESPAPELIS_LOGIN, ESPAPELIS_ADMIN, ESPAPELIS_USERNAME, ESPAPELIS_PASSWORD)
    _req = request_to_ajax(_url, _params, _session)
    """Check if status code is 200"""
    if _req.status_code != 200:
        raise Exception("The request to {0} failed".format(_url))
    """Parse content"""
    _soup = BeautifulSoup(_req.text, 'html.parser')
    """Get links"""
    _uris_raw = _soup.find_all(class_='url-res-table')
    _uris = [_uri.text for _uri in _uris_raw]
    """Publish links"""
    for _uri in _uris:
        try:
            """Add link"""
            _params_item = {
                'uri': _uri,
                'action': 'action_pelisplushd_all'
            }
            _result = request_to_ajax(_url, _params_item, _session)
            _item = None
            """Get json"""
            _item = _result.json()
            """If it was published, then add"""
            if _item['id']:
                _items.append(_item)
        except Exception as e:
            print(e)
    """Transform data"""
    _data_response = {
        "items": _items
    }
    """Return data"""
    return success_response(data=_data_response)


def request_to_ajax(url, data, session=None):
    _headers = {
        # 'accept': '*/*',
        # 'accept-encoding': 'gzip, deflate, br',
        # 'accept-language': 'es-ES,es;q=0.9,en;q=0.8',
        # 'cache-control': 'no-cache',
        # 'content-length': '33',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': 'autoptimize_feed=1; wordpress_sec_1af40cc38c0e85464967a981a9514fa0=Espapelis%7C1627370899%7CWFn4paIb5z0ePrnygXHArSiG7G5MVO6haoWevVfAV7r%7C314d0b65e1e31570765d3a9bcc10b75421e2e95170aca3138fd9014254ed0586; _ga=GA1.2.728533505.1622253102; _popfired_expires=Invalid%20Date; _popfired=1; wordpress_test_cookie=WP%20Cookie%20check; PHPSESSID=637d6fdae88c2826ad96468c08aacbdb; gainwp_wg_default_swmetric=sessions; wp-settings-time-1=1624438823; wp-settings-time-3=1625354890; wp-settings-3=editor%3Dhtml; _gid=GA1.2.1978855616.1627198102; wordpress_logged_in_1af40cc38c0e85464967a981a9514fa0=Espapelis%7C1627370899%7CWFn4paIb5z0ePrnygXHArSiG7G5MVO6haoWevVfAV7r%7C80c933b4c2e3663befb959a5bce9b66c8e5b9cc3632234fed6a3268d68d85153',
        'origin': 'https://www.espapelis.com',
        'pragma': 'no-cache',
        'Referer': 'https://www.espapelis.com/wp-admin/admin.php?page=scrappermovie-pelisplushd',
        # 'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
        # 'sec-ch-ua-mobile': '?0',
        # 'sec-fetch-dest': 'empty',
        # 'sec-fetch-mode': 'cors',
        # 'sec-fetch-site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    """Make request"""
    if session:
        _result = session.post(url, data=data)
    else:
        _result = requests.post(url, data=data, headers=_headers)
    return _result
