import urllib
from enum import Enum

import requests
from requests_toolbelt import MultipartEncoder

from m4i_analytics.m4i.auth.Auth import Auth


class ContentType(Enum):

    """
    This class enumerates various content types. Use these values to specify what kind of result you expect from your request.
    """

    TEXT = 'text'
    JSON = 'json'
    BINARY = 'binary'
    RAW = 'raw'

    @classmethod
    def is_valid(cls, value):
        """
        Check whether the provided value matches with one of the defined content types

        :returns: bool: whether or not the provided value is a defined content type

        :param any value: The value you want to check against the defined content types        
        """

        return isinstance(value, ContentType) or any(value == item.value for item in cls)
    # END is_valid
# END ContentType


class ApiUtils():

    """
    This class provides various utility functions for API classes that connect with Models4Insight.
    """

    __API_USER = 'p'

    @staticmethod
    def get(url, params={}, contentType=ContentType.TEXT, proxies={}, use_default_proxies=True, username=None, password=None, totp=None, access_token=None):
        """
        Make a HTTP GET request with the given parameters to the given url. Specify what kind of result you expect by providing the content type.

        :returns: The response of the server, parsed to the specified content type (TEXT by default).

        :param str url: The url to which the request will be made.
        :param dict params: *Optional*. The parameters to provide with the request. By default, no parameters will be provided.
        :param ContentType contentType: *Optional*. The type of result you are expecting. By default, the content type is set to TEXT.
        :param proxies: *Optional*. Add http proxy information to allow writing data while being behind a proxy.
        :param use_default_proxies *Optional*. Proxies can be set in the operating system and might be available to python. 
                With this option you can deliberately disable proxy settings in the environment.

        :exception TypeError: Thrown when the url, params and/or contentType are not defined.
        :exception ValueError: Thrown when the url, params and/or contentType are not valid.
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant.
        """

        if url is None:
            raise TypeError('Request URL is not defined')
        elif type(url) != type(str()):
            raise ValueError('Request URL is not valid')
        elif params is None:
            raise TypeError('Params is not defined')
        elif not isinstance(params, dict):
            raise ValueError('Params is not valid')
        elif contentType is None:
            raise TypeError('Content type is not defined')
        elif not ContentType.is_valid(contentType):
            raise ValueError('Content type is not valid')

        if isinstance(contentType, ContentType):
            contentType = contentType.value

        # Create the session and set the proxies.
        s = requests.Session()
        if access_token is not None or (username is not None and password is not None):
            s = ApiUtils._authorize(s, username, password, totp, access_token)

        if proxies != {}:
            s.proxies = proxies
        if use_default_proxies == False:
            s.trust_env = False
        params_encoded = urllib.parse.urlencode(
            {key: value for key, value in params.items() if value is not None},
            quote_via=urllib.parse.quote
        )
        return ApiUtils._handle_response(s.get(url, params=params_encoded), contentType)
    # END get

    @staticmethod
    def post(url, data={}, file=None, contentType=ContentType.TEXT, proxies={}, use_default_proxies=True, username=None, password=None, totp=None, access_token=None):
        """
        Make a HTTP POST request with the given data to the given url. Specify what kind of result you expect by providing the content type.

        :returns: The response of the server, parsed to the specified content type (TEXT by default).

        :param str url: The url to which the request will be made
        :param dict data: *Optional*. The data to provide with the request. By default, no data will be provided.
        :param ContentType contentType: *Optional*. The type of result you are expecting. By default, the content type is set to TEXT.
        :param proxies: *Optional*. Add http proxy information to allow writing data while being behind a proxy.
        :param use_default_proxies *Optional*. Proxies can be set in the operating system and might be available to python. 
                With this option you can deliberately disable proxy settings in the environment.

        :exception TypeError: Thrown when the url, data and/or contentType are not defined
        :exception ValueError: Thrown when the url, data and/or contentType are not valid
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant
        """

        if url is None:
            raise TypeError('Request URL is not defined')
        elif type(url) != type(str()):
            raise ValueError('Request URL is not valid')
        elif data is None:
            raise TypeError('Data is not defined')
        elif not isinstance(data, dict):
            raise ValueError('Data is not valid')
        elif contentType is None:
            raise TypeError('Content type is not defined')
        elif not ContentType.is_valid(contentType):
            raise ValueError('Content type is not valid')

        if isinstance(contentType, ContentType):
            contentType = contentType.value

        if file is not None:
            data['file'] = (file.name, file, 'application/octet-stream')
            data = MultipartEncoder(fields=data)

        # Create the session and set the proxies.
        s = requests.Session()
        if access_token is not None or (username is not None and password is not None):
            s = ApiUtils._authorize(s, username, password, totp, access_token)

        if proxies != {}:
            s.proxies = proxies
        if use_default_proxies == False:
            s.trust_env = False

        request = s.post(url, data=data)

        return ApiUtils._handle_response(request, contentType)
    # END post

    @staticmethod
    def post_file(url, data={}, file=None, contentType=ContentType.TEXT, proxies={}, use_default_proxies=True, username=None, password=None, totp=None, access_token=None):
        """
        Make a HTTP POST request with the given data to the given url. Specify what kind of result you expect by providing the content type.

        :returns: The response of the server, parsed to the specified content type (TEXT by default).

        :param str url: The url to which the request will be made
        :param dict data: *Optional*. The data to provide with the request. By default, no data will be provided.
        :param ContentType contentType: *Optional*. The type of result you are expecting. By default, the content type is set to TEXT.
        :param proxies: *Optional*. Add http proxy information to allow writing data while being behind a proxy.
        :param use_default_proxies *Optional*. Proxies can be set in the operating system and might be available to python. 
                With this option you can deliberately disable proxy settings in the environment.

        :exception TypeError: Thrown when the url, data and/or contentType are not defined
        :exception ValueError: Thrown when the url, data and/or contentType are not valid
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant
        """

        if url is None:
            raise TypeError('Request URL is not defined')
        elif type(url) != type(str()):
            raise ValueError('Request URL is not valid')
        elif data is None:
            raise TypeError('Data is not defined')
        elif not isinstance(data, dict):
            raise ValueError('Data is not valid')
        elif contentType is None:
            raise TypeError('Content type is not defined')
        elif not ContentType.is_valid(contentType):
            raise ValueError('Content type is not valid')

        if isinstance(contentType, ContentType):
            contentType = contentType.value

        # Create the session and set the proxies.
        s = requests.Session()
        if access_token is not None or (username is not None and password is not None):
            s = ApiUtils._authorize(s, username, password, totp, access_token)

        if proxies != {}:
            s.proxies = proxies
        if use_default_proxies == False:
            s.trust_env = False

        request = s.post(url, files={'file': file}, data=data)

        return ApiUtils._handle_response(request, contentType)
    # END post_file

    @staticmethod
    def post_json(url, data={}, file=None, contentType=ContentType.TEXT, proxies={}, use_default_proxies=True, username=None, password=None, totp=None, access_token=None):
        """
        Make a HTTP POST request with the given data to the given url. Specify what kind of result you expect by providing the content type.

        :returns: The response of the server, parsed to the specified content type (TEXT by default).

        :param str url: The url to which the request will be made
        :param dict data: *Optional*. The data to provide with the request. By default, no data will be provided.
        :param ContentType contentType: *Optional*. The type of result you are expecting. By default, the content type is set to TEXT.
        :param proxies: *Optional*. Add http proxy information to allow writing data while being behind a proxy.
        :param use_default_proxies *Optional*. Proxies can be set in the operating system and might be available to python. 
                With this option you can deliberately disable proxy settings in the environment.

        :exception TypeError: Thrown when the url, data and/or contentType are not defined
        :exception ValueError: Thrown when the url, data and/or contentType are not valid
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant
        """

        if url is None:
            raise TypeError('Request URL is not defined')
        elif type(url) != type(str()):
            raise ValueError('Request URL is not valid')
        elif data is None:
            raise TypeError('Data is not defined')
        elif not isinstance(data, dict):
            raise ValueError('Data is not valid')
        elif contentType is None:
            raise TypeError('Content type is not defined')
        elif not ContentType.is_valid(contentType):
            raise ValueError('Content type is not valid')

        if isinstance(contentType, ContentType):
            contentType = contentType.value
        # Create the session and set the proxies.
        s = requests.Session()
        if access_token is not None or (username is not None and password is not None):
            s = ApiUtils._authorize(s, username, password, totp, access_token)

        if proxies != {}:
            s.proxies = proxies
        if use_default_proxies == False:
            s.trust_env = False

        request = s.post(url, json=data)

        return ApiUtils._handle_response(request, contentType)
    # END post

    def delete(url, params={}, contentType=ContentType.TEXT, proxies={}, use_default_proxies=True, username=None, password=None, totp=None, access_token=None):
        """
        Make a HTTP DELETE request with the given parameters to the given url. Specify what kind of result you expect by providing the content type.

        :returns: The response of the server, parsed to the specified content type (TEXT by default).

        :param str url: The url to which the request will be made.
        :param dict params: *Optional*. The parameters to provide with the request. By default, no parameters will be provided.
        :param ContentType contentType: *Optional*. The type of result you are expecting. By default, the content type is set to TEXT.
        :param proxies: *Optional*. Add http proxy information to allow writing data while being behind a proxy.
        :param use_default_proxies *Optional*. Proxies can be set in the operating system and might be available to python. 
                With this option you can deliberately disable proxy settings in the environment.

        :exception TypeError: Thrown when the url, params and/or contentType are not defined.
        :exception ValueError: Thrown when the url, params and/or contentType are not valid.
        :exception requests.exceptions.HTTPError: Thrown when the request returned with a 400/500 code variant.
        """

        if url is None:
            raise TypeError('Request URL is not defined')
        elif type(url) != type(str()):
            raise ValueError('Request URL is not valid')
        elif params is None:
            raise TypeError('Params is not defined')
        elif not isinstance(params, dict):
            raise ValueError('Params is not valid')
        elif contentType is None:
            raise TypeError('Content type is not defined')
        elif not ContentType.is_valid(contentType):
            raise ValueError('Content type is not valid')

        if isinstance(contentType, ContentType):
            contentType = contentType.value

        # Create the session and set the proxies.
        s = requests.Session()
        if access_token is not None or (username is not None and password is not None):
            s = ApiUtils._authorize(s, username, password, totp, access_token)

        if proxies != {}:
            s.proxies = proxies
        if use_default_proxies == False:
            s.trust_env = False
        params_encoded = urllib.parse.urlencode(
            {key: value for key, value in params.items() if value is not None},
            quote_via=urllib.parse.quote
        )
        return ApiUtils._handle_response(s.delete(url, params=params_encoded), contentType)
    # END delete

    @staticmethod
    def _authorize(session, username, password, totp=None, access_token=None):
        authorization_header = 'Bearer %s' % (access_token if access_token else Auth(
        ).get_access_token(username, password, totp))
        session.headers.update({'Authorization': authorization_header})
        return session
    # END _authorize

    @staticmethod
    def _handle_response(response, contentType):

        if response is None:
            raise TypeError('HTTP response is not defined')
        elif not isinstance(response, requests.Response):
            raise ValueError('HTTP response is not valid')
        elif contentType is None:
            raise TypeError('Content type is not defined')
        elif not ContentType.is_valid(contentType):
            raise ValueError('Content type is not valid')
        # print(response.text)
        # Raises an exception if the response code is a 400/500 code (or a variant thereof)
        response.raise_for_status()

        result = None

        if contentType == ContentType.TEXT.value:
            result = response.text

        if contentType == ContentType.JSON.value:
            result = response.json()

        if contentType == ContentType.BINARY.value:
            result = response.content

        if contentType == ContentType.RAW.value:
            result = response.raw.read(10)

        return result
    # END _handle_response

# END ApiUtils
