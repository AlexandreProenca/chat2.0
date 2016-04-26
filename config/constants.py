#!/usr/bin/env python
#  -*- coding: utf-8 -*-


DATABASES = {
    'default': {
        'ENGINE': 'mysql',
        'NAME': 'nwpartner2',
        'USER': 'nwpartner2',
        'PASSWORD': 'gmmaster765',
        'HOST': '179.188.16.42',
        'PORT': '3306',
    }
}

PORT = 8888

DEBUG = False

SSL_CERT = './certs/certificate.crt'
SSL_KEY = './certs/privateKey.key'
SSL_CA = './certs/rootCA.pem'

SSL_MODE = False


