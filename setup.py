from setuptools import setup

setup(
    name='pyschematron',
    version='0.1',
    packages=['pyschematron'],
    scripts=['bin/pyschematron-check.py', 'bin/pyschematron-to-xslt.py'],
    url='https://github.com/ionite/pyschematron',
    license='MIT',
    author='Jelte Jansen',
    author_email='',
    description='An ISO schematron validator and XSLT generator'
)
