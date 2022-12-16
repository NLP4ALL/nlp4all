"""Helpers for flask and the site."""

from urllib.parse import urlparse, urljoin


def is_safe_url(target, request):
    """Ensure that the target URL is safe to redirect to."""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc
