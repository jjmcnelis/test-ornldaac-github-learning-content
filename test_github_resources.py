#!/usr/bin/env python3
import os
import sys
import json
import requests
import subprocess

# Jupyter notebook Python API:
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError




def _get_delimiter(width: int=75, char: str="#", outs: int=1, ins: int=1):
    return "{o}{c}\n{i}# {{}}\n{i}{c}\n{o}".format(
        c=char*width, o=outs*"\n", i=ins*"#\n")




def _stdout_log(message: str):
    print(message)
    __log__.write(message)




def _get_remote_json(remote_json_url: str):
    """Retrieves a remote json with `requests` and returns a dictionary.
    
    Args:
        remote_json_url (url): the url of a remote json to retrieve.
        
    Returns:
        dict: the parsed json as a dictionary.

    """
    
    # Retrieve the JSON with requests.
    response_ = requests.get(remote_json_url)

    # If the JSON was successfully retrieved, parse to a dict and return.
    if response_.ok:
        return json.loads(response_.text)
    else:
        # print("ERROR [{err}]: JSON not retrieved for '{url}'".format(
        #     err=response_.status_code, 
        #     url=remote_json_url))
        raise(Exception)




def _get_resources():
    """Retrieves or reads local reference to ORNL DAAC learning resources."""
    
    # Try to retrieve URL to retrieve Daine's 'learning.json'.
    try:
        resources_json_url_ = "https://daac.ornl.gov/js/learning.json"

        # Retrieve, load resources JSON. Resources stored in list 'data'.
        resources_ = _get_remote_json(resources_json_url_)['data']
    
    # Read from local file on failure.
    except:
        with open(os.path.join(__ws__, "resources.json"), "r") as f_:
            resources_ = json.load(f_)['data']
            
    return resources_




def _select_resources_github(resources_list: list):
    """Returns the list of GitHub resources from the list of all resources.
    
    Args:
        resources_list (list): a list of resource dictionaries.
        
    Returns:
        list: a subset of the input list containing only GitHub resources.

    """

    resources_on_github = []

    # Loop over the list of resources.
    for r in resources_list:
        
        # Append to the list if the resource is from GitHub.
        if r['url'].startswith("https://github.com/"):
            resources_on_github.append(r)
            
    return resources_on_github
   
   
   

def _get_repo_contents(repo_url: str):
    """Returns a dictionary of repository contents via GitHub API.
    
    Args:
        repo_url (url): the url of a GitHub repository.
        
    Returns:
        dict: the parsed json as a dictionary.

    """

    # Flexibly drop the beginning of the repository url.
    url_tail_ = repo_url.split("github.com/")[1]

    # Get the repository owner and name/path.
    owner_, path_ = url_tail_.split("/")
    
    # Modify this string to access the repo contents via GitHub Contents API.
    contents_api_url_ = "https://api.github.com/repos/{owner}/{path}/contents"

    # Retrieve the JSON with requests.
    response_ = requests.get(contents_api_url_.format(owner=owner_, path=path_))

    # If the JSON was successfully retrieved, parse to a dict and return.
    if response_.ok:
        return json.loads(response_.text)
    else:
        # print("ERROR [{err}]: Repo content not retrieved for '{url}'".format(
        #     err=response_.status_code, 
        #     url=repo_url))
        raise(Exception)




def _check_repo_contents(contents_list: list, contents_ext: str):
    """Returns the list of files in a repo that match the requested extension.
    
    Args:
        contents_list (list): a list of repository content dictionaries from API.
        contents_ext (str): an extension to limit results.
        
    Returns:
        list: a subset of the input list containing only matches extensions.

    """

    # Loop over the input 'contents_list' dicitonaries.
    for content_dict in contents_list:
        
        # If file has an extension matching contents_ext, return True. 
        if content_dict['name'].endswith(contents_ext):
            return True
    
    # If didn't find any matches, return False.
    return False




def _update_repo_local(repo_remote_url: str):
    """Pulls/clones a repository into 'repositories/' and exits if unsuccessful.
    
    Args:
        repo_remote_url (str): GitHub URL to the repository.
        
    Returns:
        str: the path to the local repository.

    """
    _stdout_log(_get_delimiter().format("REPO: {}".format(repo_remote_url)))

    # Get the name of the repository.
    repo_name_ = repo_remote_url.split("/")[-1]
    
    # And the target path of the local repository.
    repo_path_ = os.path.join(
        __ws__, "repositories/{repo}".format(repo=repo_name_))


    # If the repository already exists, pull it.
    if os.path.isdir(repo_path_):
        _stdout_log("# REPO EXISTS LOCALLY. PULLING ... \n")
        
        # Command line arguments for a git pull.
        command_arguments_ = ['git', 'pull', 'origin', 'master']

        # The path to pull from.
        command_path_ = repo_path_
    

    # Else the repository must be cloned from the repos directory.
    else:
        _stdout_log("# REPO DOES NOT EXIST LOCALLY. CLONING ... \n")

        # Command line arguments for a git clone.
        command_arguments_ = ['git', 'clone', repo_remote_url]

        # The path to clone from.
        command_path_ = os.path.join(__ws__, "repositories/")


    # Call the git command line utility to pull/clone.
    stdout_output = subprocess.run(
        command_arguments_,
        
        # The path to execute the system command from.
        cwd=command_path_,

        # Capture the output.
        stdout=subprocess.PIPE

    )
    
    return repo_path_  # Return the path!




def _write_exception(e):
    """Write information about the exception to the log file.
    
    Args:
        e: a thrown exception to append to the log.
    
    """
    __log__.write("  Exception [ {eclass} ]:".format(eclass=e.__class__))
    __log__.write(str(e))




_success_message = "\n  SUCCESS! Notebook saved here: {nb}"
_exception_message = """  
  ERROR! Exception message & traceback copied to: tests/LOG.txt
  
  The notebook executed up to the point of failure was saved here:
  {nb}

"""




def _test_ipynb(notebook_path: str, execute_path: str):
    """Execute ipynb with ipynb API, saves to tests folder, capturing metadata.
    
    API docs: https://nbconvert.readthedocs.io/en/latest/execute_api.html
    
    Args:
        notebook_path (str): path to the notebook to run.
        execute_path (str): path to the folder to execute from.
        
    Returns:
        dict: Metadata about the run.

    """
    # Get the output directory, file name.
    output_name_ = os.path.basename(notebook_path)
    output_dir_ = os.path.join(__ws__, "tests/{}".format(
        os.path.basename(execute_path)))
    
    # Get full path to the output file.
    output_file_ = os.path.join(output_dir_, output_name_)
    
    # Point out the discovered notebooks.
    _stdout_log("\n# PROCESSING: {} \n".format(output_name_))
                
    # Ensure the 'tests/<REPOSITORY>/' directory exists locally.
    if not os.path.isdir(output_dir_):
        os.makedirs(output_dir_)


    # Open the notebook and with Python's TextIO context manager.
    with open(notebook_path) as f_:

        # And read it with the notebook API's reader function.
        notebook_ = nbformat.read(f_, as_version=4)
    
    # Get the name of the kernel from the notebook's internal metadata.
    notebook_kernel_ = notebook_['metadata']['kernelspec']['name'] 

    # Point out the discovered notebooks.
    _stdout_log("  Notebook kernel: {} \n".format(notebook_kernel_))


    # Configure the notebook runner.
    processor_ = ExecutePreprocessor(timeout=900, kernel_name=notebook_kernel_)

    try:
        # Execute notebook ('path' is the dir to execute inside of).
        processor_.preprocess(notebook_, {'metadata': {'path': execute_path}})

    # Ignore any exceptions during notebook execution, but print a message.
    except CellExecutionError as e:
        print(_exception_message.format(nb=output_file_))
        _write_exception(e)

    # If no exceptions were thrown, document the success!
    else:
        print(_success_message.format(nb=output_file_))
        __log__.write(_success_message.format(nb=output_file_))

    # Save notebook even if Exceptions are thrown.
    finally:

        # Open a new file with Python's TextIO context manager and write output.
        with open(output_file_, 'w', encoding='utf-8') as f_:
            nbformat.write(notebook_, f_)




def _test_repo_ipynbs(repo_url: str):
    """Execute ipynb with ipynb API, saves to tests folder, capturing metadata.
    
    API docs: https://nbconvert.readthedocs.io/en/latest/execute_api.html
    
    Args:
        repo_url (str): URL to a GitHub repository to process for notebooks.

    """

    # Update the local repository by clone/pull and get the path.
    repo_path_ = _update_repo_local(repo_url)

    # Walk the repository directory.
    for _, dirs_, files_ in os.walk(repo_path_):
        
        # Exclude any '.ipynb_checkpoints'.
        dirs_[:] = [d for d in dirs_ if d!=".ipynb_checkpoints"]
        
        # Loop over the files.
        for f_ in files_:
            
            # If the file has a notebook extension, process it.
            if f_.endswith(".ipynb"):
                
                # Get the local path to the notebook.
                ipynb_ = os.path.join(repo_path_, f_)

                # Call the notebook tester function.
                _test_ipynb(notebook_path=ipynb_, execute_path=repo_path_)




if __name__ == "__main__":

    # The script execution directory.
    __ws__ = "/data"

    # Open a file for logging.
    __log__ = open(os.path.join(__ws__, "tests/LOG.txt"), "w")

    # Get the ORNL DAAC learning resources (from remote or local file).
    resources_ = _get_resources()

    # Identify the resources that live on GitHub.
    resources_github_ = _select_resources_github(resources_)

    # Loop over the repositories ...
    for repo_ in resources_github_:

        # Get the GitHub URL of the current repository.
        repo_url_ = repo_['url']
        
        # Get the contents at the URL via GitHub's API ...
        try:
            repo_contents_ = _get_repo_contents(repo_url_)
            
            # If the contents include an IPython notebook anywhere, process.
            if _check_repo_contents(repo_contents_, ".ipynb"):
                
                # Call the notebook repository processor function.
                _test_repo_ipynbs(repo_url_)
        
        # If an exception was thrown, API rate limit was likely reached.
        except:
            
            # Get the list of local repositories.
            repositories_ = os.listdir(os.path.join(__ws__, "repositories/"))
            
            # If the repository is in the 'repositories' directory, process.
            if os.path.basename(repo_url_) in repositories_:
                _test_repo_ipynbs(repo_url_)


    # Close the log file.
    __log__.close()
