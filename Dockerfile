FROM osgeo/gdal:ubuntu-full-latest

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND noninteractive

###############################################################################
# Install geospatial/data software libraries
###############################################################################

###############################################################################
# GDAL's ubuntu-full-latest image is almost complete. Update and make sure 
# core requirements for Python are installed for both Python 2 and 3.
###############################################################################

# Run a system update. Install python-dev, -pip, -numpy.
RUN apt-get update && apt-get install -y \
    python-dev \
    python-pip \
    python3-pip \
    python3-dev

# Install the data software and their Python interfaces.
RUN apt-get update && apt-get install -y \
    # Numpy for Python 2 and 3.
    python-numpy \
    python3-numpy \
    # NetCDF base and developer.
    libnetcdf-dev \
    netcdf-bin \
    # GDAL for Python 2 and 3.
    python3-gdal \
    python-gdal

# Install Python 3 interfaces to data softwares, matplotlib, jupyter.
RUN pip3 install \
    requests \
    rasterio \
    fiona \
    pandas \
    h5py \
    netCDF4 \
    shapely \
    matplotlib \
    jupyter \
    jupytext

# Install Python 2 interfaces to data softwares, matplotlib, jupyter. 
# Python 2 also doesn't ship with 'requests'.
RUN pip install \
    requests \
    rasterio \
    fiona \
    pandas \
    h5py \
    netCDF4 \
    shapely \
    matplotlib \
    jupyter \
    jupytext


###############################################################################
# Install R and packages
###############################################################################

# Install R + IRKernel dependencies that don't play nice with CRAN.
RUN apt-get install -y r-base-dev r-cran-nloptr \
	&& apt-get clean \
	&& apt-get remove \
	&& rm -rf /var/lib/apt/lists/*

# Set default R CRAN repo.
RUN echo 'options("repos"="http://cran.rstudio.com")' >> /usr/lib/R/etc/Rprofile.site

# Install R Packages and kernel for Jupyter notebook.
RUN Rscript -e "install.packages(c('devtools', 'ggplot2', 'viridis', 'plyr', 'reshape2', 'dplyr', 'tidyr', 'psych', 'pwr', 'STAR', 'ez', 'bursts', 'httr'))"
RUN Rscript -e "install.packages('IRkernel')"
RUN Rscript -e "IRkernel::installspec()"


###############################################################################
# Configure Jupyter notebook
###############################################################################

RUN jupyter notebook --generate-config && ipython profile create

# Configure notebook for 'jupytext'.
RUN echo "c.NotebookApp.open_browser = False" >> /root/.jupyter/jupyter_notebook_config.py && \
    echo "c.InteractiveShellApp.matplotlib = 'inline'" >> /root/.ipython/profile_default/ipython_config.py && \
    echo "c.NotebookApp.contents_manager_class = 'jupytext.TextFileContentsManager'" >> /root/.jupyter/jupyter_notebook_config.py

# Install notebook kernel for Python 2.7.
RUN python2 -m pip install ipykernel
RUN python2 -m ipykernel install --user


###############################################################################
# Install stuff I forgot ...
###############################################################################

RUN apt-get update && apt-get install -y git


###############################################################################
# Set up the ORNL DAAC's GitHub tester script.
###############################################################################

# Copy test runner Python script into the container.
COPY ./test_github_resources.py /opt/test_github_resources.py

# Make the module executable.
RUN chmod +x /opt/test_github_resources.py

# Create symlink to module script in the /usr/bin directory.
RUN ln -s /opt/test_github_resources.py /usr/bin/test_github_resources

# Mount points for 'repositories' and 'tests'.
VOLUME ["/data/repositories"]
VOLUME ["/data/tests"]

# Set the working directory to the data folder.
WORKDIR /data

# Copy the resources JSON into the container.
COPY ./resources.json /data/resources.json

# ENTRYPOINT tells docker to run image as an application.
ENTRYPOINT ["test_github_resources"]
