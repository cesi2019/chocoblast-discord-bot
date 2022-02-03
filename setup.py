from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
   name="chocoblast-sonar",
   version="1.0",
   description="",
   packages=["chocoblast-sonar"],
   package_data={
       "chocoblast-sonar": ["migrations/*.sql"]
   },
   install_requires=required
)