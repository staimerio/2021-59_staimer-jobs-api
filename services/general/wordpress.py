"""Services for wordpress utils"""
# Retic
from retic import App as app

# Requests
import requests


# Constants

def login(wp_login, wp_admin, username, password):

    with requests.Session() as session:
        headers1 = {'Cookie': 'wordpress_test_cookie=WP Cookie check'}
        data = {
            'log': username, 'pwd': password, 'wp-submit': 'Log In',
            'redirect_to': wp_admin, 'testcookie': '1'
        }
        session.post(wp_login, headers=headers1, data=data)        
        return session
