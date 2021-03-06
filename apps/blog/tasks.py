# coding:utf-8

from __future__ import absolute_import, unicode_literals

import urllib2
import json
import logging

from django.core.cache import cache
from celery import shared_task
from blog.models import Article, Category, Tag, BlogComment, UserProfile, VisitorIP
from configs import settings

IP_INFO_URL = 'http://int.dpool.sina.com.cn/iplookup/iplookup.php?format=json&ip='

logger = logging.getLogger('web')


@shared_task
def add(x, y):
    return x + y


@shared_task
def save_client_ip(client_ip, article=None, referer=None):
    country = ''
    city = ''
    ip_info = ''
    visitor_num = cache.get('visitor_num')
    logger.info("visitor_num: %s", visitor_num)
    if not visitor_num:
        visitor_num = VisitorIP.objects.count()
        logger.info("visitor_num in redis is None, and visitor_num is: %s", visitor_num)
        cache.set('visitor_num', visitor_num, settings.REDIS_TIMEOUT)
    last_ip = VisitorIP.objects.first()
    if not last_ip or last_ip.ip != client_ip or last_ip.article != article:
        url = IP_INFO_URL + client_ip
        try:
            ip_info = urllib2.urlopen(url)
            ip_info = ip_info.read()
        except Exception, e:
            logging.info(url)
            logging.error('Get ip info failed: %s' % e)
        if ip_info:
            ip_info = json.loads(ip_info)
            country = ip_info.get('country', '').encode('utf-8')
            city = ip_info.get('city', country).encode('utf-8')
    else:
        return 'existed ip'
    if article:
        article = Article.objects.get(id=article)
    VisitorIP.objects.create(ip=client_ip, country=country, city=city,
                             article=article, referer=referer)
    cache.set('visitor_num', visitor_num + 1, settings.REDIS_TIMEOUT)
    logger.info("update visitor_num success")
