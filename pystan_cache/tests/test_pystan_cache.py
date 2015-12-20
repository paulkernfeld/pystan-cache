from datetime import timedelta
from random import random
from tempfile import NamedTemporaryFile, TemporaryFile
from time import sleep

from mock import Mock, patch
from pytest import raises

from pystan_cache.pystan_cache import caching_stan, CachingPyStan
from pystan_cache.utils import Timer


# This is obviously nondeterministic but it has in fact helped me to catch a
# bug!
MIN_SPEEDUP_FACTOR = 10


model_code = """
data {
  int<lower=0> N;
  vector[N] x;
}
parameters {
  real beta;
} model {
  x ~ uniform(0.0, beta);
}
"""
N = 10000
beta = 1.0
stan_data = {
    "N": N,
    "x": [random() * beta for _ in xrange(N)]
}


def test_called_with_args(tmpdir):
    """
    We'll throw a ValueError if the user passes in positional arguments.

    :param str tmpdir: a temp directory (this is a built-in pytest fixture)
    """
    caching_pystan = CachingPyStan(cache_dir=str(tmpdir))

    with raises(ValueError):
        caching_pystan.stan_model("whatever")


def test_cache_code_files(tmpdir):
    """
    Code files with the same contents should cache.

    :param str tmpdir: a temp directory (this is a built-in pytest fixture)
    """
    caching_pystan = CachingPyStan(cache_dir=str(tmpdir))

    # Pass in a file object
    with TemporaryFile() as code_file_1:
        code_file_1.write(model_code)
        code_file_1.seek(0)
        with Timer() as slow_timer:
            model1 = caching_pystan.stan_model(file=code_file_1)

    # Pass in the name of the file
    with NamedTemporaryFile() as code_file_2:
        code_file_2.write(model_code)
        code_file_2.seek(0)
        with Timer() as fast_timer:
            model2 = caching_pystan.stan_model(file=code_file_2.name)

    assert model1 is model2
    assert slow_timer.interval > fast_timer.interval * MIN_SPEEDUP_FACTOR


def test_cached_memory(tmpdir):
    """
    The same model code should be reused in-memory

    :param str tmpdir: a temp directory (this is a built-in pytest fixture)
    """
    caching_pystan = CachingPyStan(cache_dir=str(tmpdir))

    with Timer() as slow_timer:
        model1 = caching_pystan.stan_model(model_code=model_code)

    with Timer() as fast_timer:
        model2 = caching_pystan.stan_model(model_code=model_code)

    assert model1 is model2

    assert slow_timer.interval > fast_timer.interval * MIN_SPEEDUP_FACTOR


def test_cached_fs(tmpdir):
    """
    The same model code should be reused from the filesystem

    :param str tmpdir: a temp directory (this is a built-in pytest fixture)
    """
    caching_pystan = CachingPyStan(cache_dir=str(tmpdir))

    with Timer() as fast_timer:
        model1 = caching_pystan.stan_model(model_code=model_code)

    # Delete the key from the cache, leaving it only as a file
    cached_model_key, = caching_pystan._cache._loaded.keys()
    del caching_pystan._cache._loaded[cached_model_key]

    with Timer() as slow_timer:
        model2 = caching_pystan.stan_model(model_code=model_code)

    # These can't be the same Python object
    assert model1 is not model2

    # StanModel does not implement `__eq__`
    assert model1.module_name == model2.module_name

    print slow_timer.interval, fast_timer.interval
    assert slow_timer.interval < fast_timer.interval * MIN_SPEEDUP_FACTOR


def test_different_model_code(tmpdir):
    """
    Different model code should be cached differently

    :param str tmpdir: a temp directory (this is a built-in pytest fixture)
    """
    # A slight variant on the model code
    model_code_alt = model_code + " "

    caching_pystan = CachingPyStan(cache_dir=str(tmpdir))
    model1 = caching_pystan.stan_model(model_code=model_code)
    model2 = caching_pystan.stan_model(model_code=model_code_alt)

    assert model1 != model2


def test_dont_cache_error(tmpdir):
    """
    Don't cache a model that throws an error. This is useful for problems with
    Stan itself, e.g. if Stan itself didn't build and link correctly.

    :param str tmpdir: a temp directory (this is a built-in pytest fixture)
    """
    caching_pystan = CachingPyStan(cache_dir=str(tmpdir))
    mock = Mock(side_effect=Exception('Boom!'))
    with raises(Exception):
        with patch("pystan.api.stanc", new=mock):
            caching_pystan.stan_model(model_code=model_code)

    # This call should not return the crashed model
    caching_pystan.stan_model(model_code=model_code).sampling(stan_data)


def test_cache_timeout(tmpdir):
    """
    When the cache times out, we should get a fresh model.

    :param str tmpdir: a temp directory (this is a pytest built-in fixture)
    """
    caching_pystan = CachingPyStan(
        cache_dir=str(tmpdir),
        timeout=timedelta(seconds=1)
    )
    model1 = caching_pystan.stan_model(model_code=model_code)
    sleep(2)
    model2 = caching_pystan.stan_model(model_code=model_code)

    assert model1 is not model2


def test_shortcut():
    """
    Make sure that the "shortcut" method of creating the cache works correctly.
    """
    with Timer() as slow_timer:
        caching_stan.stan(model_code=model_code, data=stan_data)

    with Timer() as fast_timer:
        caching_stan.stan(model_code=model_code, data=stan_data)

    assert slow_timer.interval > fast_timer.interval * MIN_SPEEDUP_FACTOR
