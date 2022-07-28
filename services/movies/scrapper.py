"""Services for hentaistube controller"""
# Retic
from retic import App as app

# Requests
import requests

# bs4
from bs4 import BeautifulSoup
from retic.services.responses import success_response

# Time
from datetime import datetime

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
    origin,
    _page=1,
):
    _items = []
    _url = '{0}/wp-admin/admin-ajax.php'.format(wp_url)
    _params = {
        u'range': _page,
        u'action': "action_{0}".format(origin)
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
                'action': 'action_{0}_all'.format(origin)
            }
            _result = request_to_ajax(_url, _params_item, _session)
            _item = None
            """Get json"""
            _item = _result.json()
            """If it was published, then add"""
            if 'id' in _item:
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
    origin,
    _page=1,
):
    _items = []
    """Find in database"""
    _session = app.apps.get("db_sqlalchemy")()
    _item = _session.query(Scrapper).\
        filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['movies']).\
        first()

    _date = datetime.now()

    if not _item or (_item.created_at.year != _date.year or _item.created_at.day != _date.day):
        print("*********scrapper_movies_publish*********")
        """Variables"""
        _items = scrapper_movies_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _page,
        )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_items) == 0):
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

        _items = scrapper_movies_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _item.value,
        )

        if(len(_items) == 0):
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)

        _session.commit()
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


def scrapper_series(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    origin,
    _page=1,
):
    _items = []
    """Find in database"""
    _session = app.apps.get("db_sqlalchemy")()
    _item = _session.query(Scrapper).\
        filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['shows']).\
        first()

    _date = datetime.now()

    if not _item or (_item.created_at.year != _date.year or _item.created_at.day != _date.day):
        print("*********scrapper_series_publish*********")
        """Variables"""
        _items = scrapper_series_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _page,
        )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_items) == 0):
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

        _items = scrapper_series_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _page,
        )

        if(len(_items) == 0):
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)

        _session.commit()
        _session.close()

    """Transform data"""
    _data_response = {
        "items": _items
    }
    """Return data"""
    return success_response(data=_data_response)


def scrapper_series_publish(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    origin,
    _page=1,
):
    _items = []
    _url = '{0}/wp-admin/admin-ajax.php'.format(wp_url)
    _params = {
        u'range': _page,
        u'action': "action_{0}_series".format(origin)
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
                'action': 'action_{0}_series_all'.format(origin)
            }
            _result = request_to_ajax(_url, _params_item, _session)
            _item = None
            """Get json"""
            _item = _result.json()
            """If it was published, then add"""
            if 'serie_id' in _item:
                _items.append(_item)
        except Exception as e:
            print(e)

    print("*********return _items*********")
    print(len(_items))
    return _items


def scrapper_torrents(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    origin,
    _page=1,
):
    _items = []
    """Find in database"""
    _session = app.apps.get("db_sqlalchemy")()
    _item = _session.query(Scrapper).\
        filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['torrents']).\
        first()

    _date = datetime.now()

    if not _item or (_item.created_at.year != _date.year or _item.created_at.day != _date.day):
        print("*********scrapper_torrents_publish*********")
        """Variables"""
        _items = scrapper_torrents_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _page,
        )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_items) == 0):
        print("*********if _item is None*********")
        if _item is None:
            print("*********_item = Scrapper*********")
            _item = Scrapper(
                key=wp_url,
                type=constants.TYPES['torrents'],
                value=_page+1
            )
            """Save chapters in database"""
            _session.add(_item)
            _session.flush()

        _items = scrapper_torrents_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _item.value,
        )

        if(len(_items) == 0):
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)

        _session.commit()
        _session.close()

    """Transform data"""
    _data_response = {
        "items": _items
    }
    """Return data"""
    return success_response(data=_data_response)


def scrapper_torrents_publish(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    origin,
    _page=1,
    category=""
):
    _items = []
    _url = '{0}/wp-admin/admin-ajax.php'.format(wp_url)
    _params = {
        u'range': _page,
        u'unique': "",
        u'action': "action_preview_todo_series",
        u'categoria': category,
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
            _category_old = category
            _cat = ""
            if not category:
                if 'serie' in _uri:
                    category = "series"
                    if '4k' in _uri.lower():
                        _cat = "series-4k"
                    else:
                        _cat = "series"
                    _cat = "series"
                elif 'pelicula' in _uri:
                    category = "peliculas"
                    if 'hd' in _uri.lower():
                        _cat = "peliculas-hd"
                    else:
                        _cat = "peliculas"
                elif 'documental' in _uri:
                    category = "peliculas"
                    _cat = "documentales"
                elif 'musica' in _uri:
                    category = "peliculas"
                    _cat = "musica"
                elif 'juego' in _uri:
                    category = "peliculas"
                    _cat = "juegos"
            """Add link"""
            _params_item = {
                'typ': category,
                'cat': _cat,
                'uri': _uri,
                'action': 'action_todo_{0}'.format(category)
            }
            _result = request_to_ajax(_url, _params_item, _session)
            _item = None
            """Get json"""
            _item = _result.json()
            """If it was published, then add"""
            if 'serie_id' in _item:
                _items.append(_item)
            category = _category_old
        except Exception as e:
            print(e)

    print("*********return _items*********")
    print(len(_items))
    return _items


def scrapper_hentai(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    origin,
    _page=1,
):
    _items = []
    """Find in database"""
    _session = app.apps.get("db_sqlalchemy")()
    _item = _session.query(Scrapper).\
        filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['hentai']).\
        first()

    _date = datetime.now()

    if not _item or (_item.created_at.year != _date.year or _item.created_at.day != _date.day):
        print("*********scrapper_hentai_publish*********")
        """Variables"""
        _items = scrapper_hentai_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _page,
        )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_items) == 0):
        print("*********if _item is None*********")
        if _item is None:
            print("*********_item = Scrapper*********")
            _item = Scrapper(
                key=wp_url,
                type=constants.TYPES['hentai'],
                value=_page+1
            )
            """Save chapters in database"""
            _session.add(_item)
            _session.flush()

        _items = scrapper_hentai_publish(
            wp_login,
            wp_admin,
            wp_username,
            wp_password,
            wp_url,
            origin,
            _item.value,
        )

        if(len(_items) == 0):
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)

        _session.commit()
        _session.close()

    """Transform data"""
    _data_response = {
        "items": _items
    }
    """Return data"""
    return success_response(data=_data_response)


def scrapper_hentai_publish(
    wp_login,
    wp_admin,
    wp_username,
    wp_password,
    wp_url,
    origin,
    _page=1,
    category=""
):
    _items = []
    _url = '{0}/wp-admin/admin-ajax.php'.format(wp_url)
    _params = {
        u'range': _page,
        u'unique': "",
        u'action': "action_preview_todo_series",
        u'categoria': category,
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
            _category_old = category
            _cat = ""
            if not category:
                if 'serie' in _uri:
                    category = "series"
                    if '4k' in _uri.lower():
                        _cat = "peliculas-4k"
                    else:
                        _cat = "peliculas"
                    _cat = "peliculas"
                elif 'pelicula' in _uri:
                    category = "peliculas"
                    if 'hd' in _uri.lower():
                        _cat = "series-hd"
                    else:
                        _cat = "series"
                elif 'documental' in _uri:
                    category = "peliculas"
                    _cat = "documentales"
                elif 'musica' in _uri:
                    category = "peliculas"
                    _cat = "musica"
                elif 'juego' in _uri:
                    category = "peliculas"
                    _cat = "juegos"
            """Add link"""
            _params_item = {
                'typ': category,
                'cat': _cat,
                'uri': _uri,
                'action': 'action_todo_{0}'.format(category)
            }
            _result = request_to_ajax(_url, _params_item, _session)
            _item = None
            """Get json"""
            _item = _result.json()
            """If it was published, then add"""
            if 'serie_id' in _item:
                _items.append(_item)
            category = _category_old
        except Exception as e:
            print(e)

    print("*********return _items*********")
    print(len(_items))
    return _items
