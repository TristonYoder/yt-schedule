from setuptools import setup

setup(
    name='yt-schedule',
    version='2.2.0',
    description='YouTube Stream Scheduler - Automate scheduling of YouTube live broadcasts',
    author='Your Name',
    py_modules=['main'],
    install_requires=[
        'google-api-python-client==2.108.0',
        'google-auth==2.25.2',
        'google-auth-httplib2==0.2.0',
        'google-auth-oauthlib==1.2.0',
        'python-dotenv==1.0.0',
    ],
    entry_points={
        'console_scripts': [
            'yt-schedule=main:main',
        ],
    },
    python_requires='>=3.9',
)

