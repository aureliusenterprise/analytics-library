from setuptools import setup, find_packages


setup(
      name="m4i-analytics",
      version = "0.1.0",
      url="http://gitlab.com/m4i/analytics-library",
      author="Aurelius Enterprise",
      packages=find_packages(),
      install_requires=["enum-compat","future","graphviz","matplotlib","networkx","pandas","pydotplus","requests","requests-toolbelt", "rx", "sqlalchemy","sqlparse","uuid", "python-keycloak"],
      zip_safe=False
)
