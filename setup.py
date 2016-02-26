from setuptools import setup, find_packages


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Django',
    'Intended Audience :: Developers',
    'License :: Public Domain',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    'Topic :: Software Development',
    'Topic :: Software Development :: Libraries :: Application Frameworks',
]

setup(
    author="Daniel Boczek",
    author_email="daniel.boczek@gmail.com",
    name='elasticdj',
    version='1.0rc1',
    description='Reusable app for Django to help create and manage elasticsearch Doctypes from Models',
    # long_description=open(os.path.join(os.path.dirname(__file__), 'README.md')).read(),
    url='https://github.com/dboczek/elasticdj',
    license='Public Domain',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    install_requires=[
        'django>=1.7',
        'elasticsearch>=1.9.0',
        'elasticsearch-dsl>=0.0.10',
    ],
    # tests_require=[
    # ],
    packages=find_packages(exclude=["project", "project.*"]),
    include_package_data=True,
    zip_safe=True,
)
