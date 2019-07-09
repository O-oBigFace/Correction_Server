# -*- coding: utf-8 -*-

from django.views.decorators.csrf import csrf_exempt
from sementic_server.source.intent_extraction.item_matcher import ItemMatcher
from django.http import JsonResponse
import timeit
import json
import logging
logger = logging.getLogger("server_log")

item_matcher = ItemMatcher(True)


@csrf_exempt
def correct(request):
    """
    纠错模块单独测试接口
    :param request:
    :return:
    """
    print(request.method)

    if request.method != 'POST':
        logger.error("仅支持post访问")
        return JsonResponse({"result": {}, "msg": "仅支持post访问"}, json_dumps_params={'ensure_ascii': False})
    try:
        request_data = json.loads(request.body)
    except Exception:
        request_data = request.POST
    print(request)
    sentence = request_data['sentence']
    account = None
    need_correct = request_data.get('need_correct', True)

    start_time = timeit.default_timer()
    result = dict()
    try:
        result = item_matcher.match(sentence, need_correct, account)
        end_time = timeit.default_timer()
        logger.info("intent_extraction - time consume: {0} S.\n".format(end_time - start_time))
    except Exception as e:
        logger.error(f"intent_extraction - {e}")
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
