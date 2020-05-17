from setuptools import setup

setup(
    name='pyschematron',
    version='0.1',
    packages=['pyschematron'],
    scripts=['bin/pyschematron-validate.py', 'bin/pyschematron-convert.py'],
    url='https://github.com/ionite/pyschematron',
    license='MIT',
    author='Jelte Jansen',
    author_email='',
    description='An ISO schematron validator and XSLT generator'
)
