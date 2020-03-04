# Auto-test ORNL DAAC GitHub Resources

The script in this repo ([test_github_resources.py](test_github_resources.py)) will test all of the Jupyter notebook-based learning resources on the ORNL DAAC GitHub, capturing the points of failure in [tests/log.txt](tests/log.txt).

## usage

This script is meant to run in Docker because of the unusual requirements of multiple Python versions + R + a Jupyter install configured to run against all three.

### run the container

```shell
docker run \
  -v /FULL/PATH/TO/REPO/repositories:/data/repositories \
  -v /FULL/PATH/TO/REPO/tests:/data/tests \
  --rm -it ornldaac-github-tests
```

### rebuild the container

```shell
docker build -t ornldaac-github-tests
```

## how it works

In several steps:

1. Downloads the reference JSON pointing to ORNL DAAC's learning resources (maintained by daine: https://daac.ornl.gov/js/learning.json), or reads it from local copy [(resources.json)](resources.json) if it's inaccessible.

2. Selects resources that point to URLs beginning with *`https://github.com/`*

3. Determines which repositories contain Jupyter notebooks (Python 2, Python 3, and R) by accessing their contents via the GitHub API.

4. Clones/pulls the selected repositories into [repositories/](repositories/).

5. Using the `notebooks` Python API, processes all the `ipynb` files and captures any raised exceptions in a log written to [`tests/`](tests/). The notebook state when execution terminates is written into subfolder for the corresponding repo within [`tests/`](tests/). The log looks like this:

*NOTE: Some of the notebooks (MODIS Web Service, mainly) take a LONG time to run. I set the timeout to 15 minutes for one notebook.*

## log example

```text
###########################################################################
#
# REPO: https://github.com/ornldaac/modis
#
###########################################################################

# REPO EXISTS LOCALLY. PULLING ... 

# PROCESSING: modis-global-fixed-statistics.ipynb 
  Notebook kernel: ir
  SUCCESS! Notebook saved here: tests/modis/modis-global-fixed-statistics.ipynb

...
```

## usage without docker

You can run the Python script outside of Docker if you have some key pieces of software:

* Python 2 AND 3
* R
* Jupyter + the IRKernel for Jupyter

You need to initialize all three kernels with Jupyter or the script WILL NOT WORK. See these pages for more info:

* Python kernels: https://ipython.readthedocs.io/en/latest/install/kernel_install.html
* IRKernel: https://github.com/IRkernel/IRkernel

The ['Dockerfile'](Dockerfile) can give you some clues about how to set this up with a debian-based linux distro (and potentially wreck your system Python). But the most convenient way to get the correct setup is with `conda`.

I prefer [`miniconda`](https://docs.conda.io/en/latest/miniconda.html) because Anaconda has some much bs included. Conda has convenient installs for any version of Python, plus R, Ruby, etc.
