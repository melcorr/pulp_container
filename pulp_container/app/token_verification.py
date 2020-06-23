import re
import jwt

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


CONTENT_HOST = re.sub(r"(http://|https://)", "", settings.CONTENT_ORIGIN, count=1)


def _decode_token(encoded_token):
    """
    Decode token and verify a signature with a public key.

    If the token could not be decoded with a success, a client does not have a
    permission to operate with a registry.
    """
    JWT_DECODER_CONFIG = {
        "algorithms": [settings.TOKEN_SIGNATURE_ALGORITHM],
        "issuer": settings.TOKEN_SERVER,
        "audience": CONTENT_HOST,
    }
    with open(settings.PUBLIC_KEY_PATH, "rb") as public_key:
        try:
            decoded_token = jwt.decode(encoded_token, public_key.read(), **JWT_DECODER_CONFIG)
        except jwt.exceptions.InvalidTokenError:
            decoded_token = {"access": []}
    return decoded_token


def _access_scope(request):
    repository_path = request.resolver_match.kwargs.get("path", "")

    if request.method in ["GET", "HEAD", "OPTIONS"]:
        access_action = "pull"
    else:
        access_action = "push"

    return repository_path, access_action


def _contains_accessible_actions(decoded_token, repository_path, access_action):
    """
    Check if a client has an access permission to execute the pull/push operation.

    When a client targets the root endpoint, the verifier does not necessary need to
    check for the pull or push access permission, therefore, it is granted automatically.

    """
    for access in decoded_token["access"]:
        if repository_path == access["name"]:
            if access_action in access["actions"]:
                return True
            if not repository_path:
                return True
    return False


class TokenAuthentication(BaseAuthentication):
    """
    Token based authentication for Container Registry.
    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Bearer ".  For example:
        Authorization: Bearer 401f7ac837da42b97f613d789819ff93537bee6a
    """

    keyword = "Bearer"

    def authenticate(self, request):
        """
        Check that the provided Bearer token specifies access.
        """
        if settings.get("TOKEN_AUTH_DISABLED", False):
            return (AnonymousUser(), None)

        try:
            authorization_header = request.headers["Authorization"]
        except KeyError:
            raise AuthenticationFailed(
                detail="Access to the requested resource is not authorized. "
                "A Bearer token is missing in a request header.",
            )
        if not authorization_header.lower().startswith(self.keyword.lower() + " "):
            raise AuthenticationFailed(
                detail="Access to the requested resource is not authorized. "
                "A Bearer token is missing in a request header.",
            )
        token = authorization_header[len(self.keyword) + 1 :]
        decoded_token = _decode_token(token)
        repository_path, access_action = _access_scope(request)

        # Without repository_path, there is no action
        if not _contains_accessible_actions(decoded_token, repository_path, access_action):
            raise AuthenticationFailed(
                detail="Access to the requested resource is not authorized. "
                "A provided Bearer token is invalid.",
            )

        username = decoded_token.get("sub")
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise AuthenticationFailed("No such user")
        else:
            user = AnonymousUser()
        return (user, None)

    def authenticate_header(self, request):
        """
        Build a formatted authenticate string.

        For example, a created string will be the in following format:
        realm="http://localhost:123/token",service="docker.io",scope="repository:app:push"
        and will be used in the "WWW-Authenticate" header.
        """
        realm = settings.TOKEN_SERVER
        repository_path, access_action = _access_scope(request)

        authenticate_string = f'{self.keyword} realm="{realm}",service="{CONTENT_HOST}"'

        if repository_path:
            scope = f"repository:{repository_path}:{access_action}"
            authenticate_string += f',scope="{scope}"'
        return authenticate_string
