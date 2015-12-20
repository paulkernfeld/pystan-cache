from datetime import timedelta
from functools import wraps
import io
from os.path import join

from mock import patch
import pyfscache
import pystan
from pystan import __version__ as pystan_version
from pystan import StanModel
from pystan._compat import string_types


DEFAULT_CACHE_DIR = join('.cache', 'stan')
DEFAULT_CACHE_TIMEOUT = timedelta(days=7)


class CachingPyStan(object):
    """
    This object encapsulates a caching version of PyStan.
    """
    def __init__(
            self,
            cache_dir=DEFAULT_CACHE_DIR,
            timeout=DEFAULT_CACHE_TIMEOUT
    ):
        """
        Create a new PyStan cache.

        :param str|None cache_dir: the path to the cache directory
        :param timedelta|None timeout: how long until the cache expires
        """
        self._cache = pyfscache.FSCache(
            cache_dir, seconds=timeout.total_seconds()
        )

        @self._cache
        def _stan_model(pystan_version, **kwargs):
            return StanModel(**kwargs)

        self._stan_model = _stan_model

    @wraps(StanModel)
    def stan_model(self, *args, **kwargs):
        """
        :return pystan.StanModel: a PyStan StanModel, possibly from the cache
        """
        # This is useful because it avoids duplicate cache keys and it allows
        # PyStan Cache to not need to know too much about the internals of
        # PyStan. Also it's good style!
        if args:
            raise ValueError(
                "Please invoke pystan_cache using named arguments only. E.g. "
                "instead of calling `cached_stan('my_code_file')`, call "
                "`cached_stan(file='my_code_file')`."
            )

        # In order to manage the cache, we need access to the model code.
        # Therefore, if the user passes in a code file, read it into a
        # string.
        if kwargs.get("file", None) and not kwargs.get("model_code", None):
            code_file = kwargs.pop("file")
            if isinstance(code_file, string_types):
                with io.open(
                        code_file,
                        'rt',
                        encoding=kwargs.get("charset", "utf-8")
                ) as f:
                    kwargs["model_code"] = f.read()
            else:
                kwargs["model_code"] = code_file.read()

        # W/o this, the same file will cache differently depending on whether
        # it's opened as a string or as unicode.
        kwargs["model_code"] = unicode(kwargs["model_code"])

        # Now return a cached model
        return self._stan_model(pystan_version, **kwargs)

    @wraps(pystan.stan)
    def stan(self, *args, **kwargs):
        # Run PyStan's "stan" method, replacing PyStan's StanModel with our
        # own cached StanModel.
        with patch('pystan.api.StanModel', self.stan_model):
            return pystan.stan(*args, **kwargs)


# This object is a shortcut that returns a ready-to-use CachingPyStan.
caching_stan = CachingPyStan()
