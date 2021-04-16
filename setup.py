from setuptools import setup

setup(name='tiling',
      version='1.0.0',
      description='Splitting image into tiles and assembling tiles into an image',
      url='https://github.com/robertibatullin/tiling',
      author='Robert Ibatullin',
      author_email='r.ibatullin@celado-media.ru',
      packages=['tiling'],
      install_requires=[
          'numpy','Pillow'
      ],
      zip_safe=False)
