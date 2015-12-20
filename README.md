PyStan Cache
============
This is a simple [pystan](https://pystan.readthedocs.org) wrapper that
persistently caches compiled model code. While compiling a model takes seconds
or minutes, loading a cached model takes hundredths of a second (YMMV).


Usage
-----
Use this just as you would use `pystan.stan`.

```python
from pystan_cache.pystan_cache import caching_stan

model_code = "insert stan code here"
data = {"x": [1,2,3]}

# On the first run, this will be slow. Subsequent runs will be fast!
caching_stan.stan(model_code=model_code, data=data)
```

If you would like to customize the cache, you can do that too.

```python
from pystan_cache.pystan_cache import CachingPyStan

model_code = "insert stan code here"
data = {"x": [1,2,3]}
caching_stan = CachingPystan(cache_dir="C:\CACHE\STAN")

# Create a model, then fit it.
model = caching_stan.stan_model(model_code=model_code)
model.sampling(data)

# Make and fit a model.
caching_stan.stan(model_code=model_code, data=data)
```

Features
--------
* Changing the version of PyStan invalidates the cache
* Caches in-memory and on the filesystem
* Well-tested

Fine Print
----------
I have only tested this with Python 2.7, and I'm sure that it doesn't work
with Python 3.

If things are going horribly wrong, first try clearing the Stan cache, the
default location for which is `.cache/stan`.

The cached compiled code is a function of the input Stan code as well as the
pystan library that's compiling it. To ensure that changing the version of
pystan invalidates the cache, this library looks at `pystan.__version__`.
Therefore, if you modify the pystan library without changing the version
number, this library is not for you.

License
-------
Copyright 2015 Paul Kernfeld.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
