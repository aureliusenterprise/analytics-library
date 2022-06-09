# Models4Insight Analytics Library
The Models4Insight Analytics Library provides many generic functions to assist in working with models on a very granular level. Core functionalities include model generation, model analysis and model visualization. The analytics library also provides interfaces to the Models4Insight repository and Models4Insight portal.

Many functions of this library require user authentication. [Sign up for an M4I account](http://www.models4insight.com/).

## Installation
The Models4Insight Analytics Library works with `Python 2.7+` and `Python 3.6+`.

### Update installation dependencies
Before installation, please make sure the latest versions of `pip` and `setuptools` are installed:
```
pip install --upgrade setuptools pip
```

### Set up a virtual environment (Optional)
We recommend that you set up a `virtual environment` in which to install the analytics library. This creates a separate installation directory which prevents potential version conflicts with Python libraries that you may have installed. A virtual environment can be set up like this:
```
pip install virtualenv
virtualenv venv
```

This creates a new installation directory in the current folder. Next, activate the virtual environment:
```
. ./venv/bin/activate
```
The virtual environment needs to be active whenever you want to use the analytics library.

### Install the library
To install the analytics library, please navigate to the folder where you have stored the received distribution. If you have set up a virtual environment, please make sure it is activated. Next, run the following command to install the library and its dependencies:
```
pip install .
```

### Update the library
If you already have a version of the analytics library installed, and you wish to upgrade to the latest version, please run the following command from the directory in which you have stored the latest distribution:
```
pip install . --upgrade
```

### Uninstall the library
If you want to uninstall the analytics library, run the following command:
```
pip uninstall m4i_analytics
```

## Configuration
Many of the built-in library functions that interact with the Models4Insight repository and portal rely on configuration parameters. The default configuration will be suited for most users. However, it is possible  to overload the default configurations if so desired. If you are for example behind a corporate proxy, it may be necessary to update the configuration to take this into account. 

### Repository configuration
You can overload the configuration parameters for the M4I repository by including a script called `m4i_platform_config.py` in the same directory from which you are running your scripts. Alternatively, you can set up an environment variable called `M4I_PLATFORM_CONFIG` to point to the configuration file independent of the file name or the location of your other scripts.

The config script should have the following structure:
```
'''
Configurable values
'''
M4I_BASE_URI = "http://www.models4insight.com/"
REPOSITORY_BASE_URI = M4I_BASE_URI + "RestApi/"
# uncomment and set IP address and port of your proxy server
#HTTP_PROXY = "http://your.proxy.com/"
#HTTPS_PROXY ="https://your.proxy.com/"


# set this setting to False in case you want the http connections NOT to use any proxy settings.
#USE_DEFAULT_PROXIES = True
```

### Portal configuration
You can overload the configuration parameters for the M4I portal by including a script called `m4i_portal_config.py` in the same directory from which you are running your scripts. Alternatively, you can set up an environment variable called `M4I_PORTAL_CONFIG` to point to the configuration file independent of the file name or the location of your other scripts.

The config script should have the following structure:
```
'''
Configurable values 
'''
BASE_URI = "http://portal.models4insight.com/m4i/rest/"

# uncomment and set IP address and port of your proxy server
#HTTP_PROXY = "http://your.proxy.com"
#HTTPS_PROXY ="http://your.proxy.com"

# set this setting to False in case you want the http connections NOT to use any proxy settings.
#USE_DEFAULT_PROXIES = True
```

## Structure
The M4I analytics library is structured as follows:

├── m4i_analytics
│   ├── examples
│   ├── graphs
│   │   ├── languages
│   │   │   └── archimate
│   │   └── visualisations
│   ├── m4i
│   │   ├── platform
│   │   ├── portal
│   ├── model_extractor
│   ├── monitoring
│   ├── shared

### Examples
The `m4i_analytics.examples` package contains several scripts that show off what you can do with the analytics library. These scripts are intended as a starting point for your own analyses.

### Graphs
Under the `m4i_analytics.graphs` package you will find all the features related to handling a model as a graph. Modeling language specific features are implemented in the various sub-packages. Currently, the analytics library supports ArchiMate 3 (`m4i_analytics.graphs.languages.archimate`). UML and BPMN support is pending.

### M4I
The `m4i_analytics.m4i` package contains all the features related to interfacing with the Models4Insight repository and portal. All repository related functions are implemented under `m4i_analytics.m4i.platform`, and portal specific functions are implemented under `m4i_analytics.m4i.portal`.

### Model Extractor
The `m4i_analytics.model_extractor` package houses basic functionality related to mining models from various source systems. If you want to implement your own extractor, this is where to start. Premade extractors for some systems are available as extensions to the analytics library and therefore not packaged by default.

### Monitoring
The `m4i_analytics.monitoring` package contains scripts related to monitoring the status of one or more systems based on the model.

### Shared
The shared package contains several modules that are used in multiple other modules of the library. 

## Docs
You can find additional documentation on the analytics library [here](http://docs.models4insight.com/).
