from keycloak import KeycloakOpenID
import requests

if __name__ == '__main__':
    
    base_url = 'http://portal.models4insight.com/'
    login_url = base_url + 'login'
    all_slices_url = base_url + 'slicemodelview/api/read'
    all_dashboards_url = base_url + 'dashboardmodelview/api/read'
    
    keycloak_options = {
        'server_url': 'http://www.models4insight.com/auth/',
        'client_id': 'm4i_public',
        'realm_name': 'm4i',
    }
    
    keycloak_user = {
        'username': 'username',
        'password': 'password'
    }
    
    keycloak_oid = KeycloakOpenID(**keycloak_options)
    
    token = keycloak_oid.token(**keycloak_user)
    
    keycloak_cookies = requests.cookies.RequestsCookieJar()
    keycloak_cookies.set('KEYCLOAK_IDENTITY', token['access_token'])
    keycloak_cookies.set('KEYCLOAK_SESSION', token['session_state'])
    
    superset_cookies = requests.get(login_url, cookies=keycloak_cookies).cookies
    
    all_slices = requests.get(all_slices_url, cookies=superset_cookies).json()
    
    all_dashboards = requests.get(all_dashboards_url, cookies=superset_cookies).json()