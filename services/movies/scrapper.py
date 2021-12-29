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

# Models
from models import Scrapper
import services.general.constants as constants

# Constants


def scrapper_movies_publish(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    _page=1,
):
    _items = []
    _url = '{0}/wp-admin/admin-ajax.php'.format(wp_url)
    _params = {
        u'range': _page,
        u'action': "action_pelisplushd"
    }

    _session = wordpress.login(
        wp_login, wp_admin, wp_username, wp_password)
    _req = request_to_ajax(_url, _params, _session)
    print("*********wordpress.login*********")
    print(wp_login)
    print(wp_admin)
    print(wp_username)
    print(wp_password)
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

    print("*********return _items*********")
    print(len(_items))
    return _items


def scrapper_movies(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    _page=1,
):
    print("*********scrapper_movies_publish*********")
    """Variables"""
    _items = scrapper_movies_publish(
        wp_login,
        wp_admin,
        wp_username,
        wp_password,
        wp_url,
        _page,
    )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_items) == 0):
        """Find in database"""
        _session = app.apps.get("db_sqlalchemy")()
        _item = _session.query(Scrapper).\
            filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['movies']).\
            first()

        print("*********if _item is None*********")
        if _item is None:
            print("*********_item = Scrapper*********")
            _item = Scrapper(
                key=wp_url,
                type=constants.TYPES['movies'],
                value=_page+1
            )
            """Save chapters in database"""
            _session.add(_item)
            _session.flush()
            """Save in database"""
        else:
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)
        _session.commit()

        _items = scrapper_movies_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            _item.value,
        )

        _session.close()

    """Transform data"""
    _data_response = {
        "items": _items
    }
    """Return data"""
    return success_response(data=_data_response)


def request_to_ajax(url, data, session=None, _headers={}):
    """Make request"""
    if session:
        _result = session.post(url, data=data)
    else:
        _result = requests.post(url, data=data, headers=_headers)
    return _result


def scrapper_shows_publish(
    wp_url,
    _page=1,
):
    
    _url = '{0}/scrapper-ajax-pelisplus-series.php'.format(wp_url)
    _params = {
        u'range': _page,
    }
    _req = request_to_ajax(_url, _params)
    """Check if status code is 200"""
    if _req.status_code != 200:
        raise Exception("The request to {0} failed".format(_url))
    """Parse content"""
    _soup = BeautifulSoup(_req.text, 'html.parser')
    """Get links"""
    _table_raw = _soup.find(class_="tbody-res")
    _items_raw = _table_raw.findAll("tr")
    _series = []
    _episodes = []
    _serie = None
    for _item_raw in _items_raw:
        _uri = _item_raw.find(class_='url-res-table')

        if _item_raw.attrs['data-type'] == 'serie':

            if _serie:
                _serie['episodes'] = _episodes
                _series.append(_serie)
                _episodes = []

            _serie = {
                u'episodes': _item_raw.attrs['episodes'],
                u'seasons': _item_raw.attrs['seasons'],
                u'uri': _uri.text,
                u'typ': 'serie',
                u'tmdb': None,
            }
        else:
            _title = _item_raw.find(class_='title-res-table')
            try:
                _episode = _title.text.split('E-')[-1]
            except Exception as e:
                _episode = "N/A"

            _episodes.append({
                u'episode': _episode,
                u'season': _item_raw.attrs['data-season'],
                u'title': _title.text,
                u'uri': _uri.text,
                u'typ': 'episode',
                u'tmdb': None,
            })

        # _series.append()
    """Publish links"""
    _items_series = []
    _item_serie = None
    for _serie in _series:
        try:
            _url_serie = '{0}/scrapper-ajax-all-pelisplus-series.php'.format(
                wp_url)
            """Add link"""
            _params_item = {
                'uri': _serie['uri'],
                'typ': _serie['typ'],
                'seasons': _serie['seasons'],
                'episodes': _serie['episodes']
            }
            _result = request_to_ajax(_url_serie, _params_item)
            """Get json"""
            _item_serie = _result.json()
            """If it was published, then add"""
            if _item_serie['serie_id'] == 0:
                continue

            _items_episodes = []
            for _episode in _serie['episodes']:
                _url_episode = '{0}/scrapper-ajax-all-pelisplus-episodes.php'.format(
                    wp_url)
                """Add link"""
                _params_item_episode = {
                    'uri': _episode['uri'],
                    'typ': _episode['typ'],
                    'serieid': _item_serie['serie_id'],
                    'season': _episode['season'],
                    'episode': _episode['episode'],
                    'tmdb': _item_serie['tmdb']
                }
                _result_episode = request_to_ajax(
                    _url_episode, _params_item_episode)
                """Get json"""
                _item_episode = _result_episode.json()
                _items_episodes.append(_item_episode)

            _item_serie['episodes'] = _items_episodes
            _items_series.append(_item_serie)
            break

        except Exception as e:
            print(e)

    print("*********return _items*********")
    print(len(_items_series))
    return _items_series


def scrapper_shows(
    wp_url,
    _page=1,
):
    print("*********scrapper_shows_publish*********")
    """Variables"""
    _items = scrapper_shows_publish(
        wp_url,
        _page,
    )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_items) == 0):
        """Find in database"""
        _session = app.apps.get("db_sqlalchemy")()
        _item = _session.query(Scrapper).\
            filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['shows']).\
            first()

        print("*********if _item is None*********")
        if _item is None:
            print("*********_item = Scrapper*********")
            _item = Scrapper(
                key=wp_url,
                type=constants.TYPES['shows'],
                value=_page+1
            )
            """Save chapters in database"""
            _session.add(_item)
            _session.flush()
            """Save in database"""
        else:
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)
        _session.commit()

        _items = scrapper_shows_publish(
            wp_url,
            _item.value,
        )

        _session.close()

    """Transform data"""
    _data_response = {
        "items": _items
    }
    """Return data"""
    return success_response(data=_data_response)