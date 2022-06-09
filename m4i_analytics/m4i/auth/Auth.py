from keycloak import KeycloakOpenID
import m4i_analytics.m4i.auth.config as config


class _Auth:
    _instance = None

    def __init__(self):
        keycloak_config = config.KEYCLOAK_JSON
        self._keycloak_client = KeycloakOpenID(
            server_url=keycloak_config["auth-server-url"]
            , realm_name=keycloak_config["realm"]
            , client_id=keycloak_config["resource"]
        )
    # END __init__

    def get_access_token(self, username, password, totp=None):
        access_token = self._keycloak_client.token(username, password, "password").get('access_token')
        return access_token
    # END get_token
    
    def get_well_know(self):
        return self._keycloak_client.well_know()
    # END get_well_know


# END _Auth

def Auth():
    """
    Factory function for the Auth instance
    :return: The Auth singleton instance
    """

    if _Auth._instance is None:
        _Auth._instance = _Auth()
    return _Auth._instance
# END Auth
