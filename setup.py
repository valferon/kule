from distutils.core import setup

setup(name='Kule',
      version='0.3',
      description='REST Interface for MongoDB',
      author='Fatih Erikli',
      author_email='fatiherikli@gmail.com',
      url='https://github.com/fatiherikli/kule',
      packages=[
            'kule',
            'kule.contrib'
      ],
      install_requires = [
          'bottle==0.11.6',
          'pymongo>=3.0',
      ]
)
