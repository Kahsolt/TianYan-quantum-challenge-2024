#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/24 

# 图形化界面操作真机拓扑实在是太弱智了，我们需要API自动化这一切！

import os
from datetime import datetime
import requests as R

AUTH_KEY = os.getenv('AUTH_KEY')
assert AUTH_KEY, 'need set envvar AUTH_KEY, find Authorization in your browser F11'

API_URL = 'https://qc.zdxlz.com/qccp-quantum/experiments/detail'
# simulator submit: https://qc.zdxlz.com/qccp-quantum/experiment/commit
# real-chip submit: https://qc.zdxlz.com/qccp-quantum/experiments/task?name=&source=&current=1&size=5&computerId=&status=&experimentDetailId=1805172331643322369&=&a=171922416262

HEADERS = {
  'Accept': 'application/json, text/plain, */*',
  'Accept-Language': 'zh-CN,ja;q=0.8,en;q=0.5,en-US;q=0.3',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Content-Type': 'application/json',
  'Origin': 'https://qc.zdxlz.com',
  'Referer': 'https://qc.zdxlz.com/laboratory/',
  'DNT': '1',
  'TE': 'trailers',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
  'Authorization': AUTH_KEY,
  'Cookie': f'userCookie={AUTH_KEY}',
  'requestTime': datetime.strftime(datetime.now(), '%m/%d/%Y, %I:%M:%S %p'),
  'apiCode': 'detail',
}


# 线路名称和ID，先主动创建再用此脚本更新
CIRCUIT_NAME = 'Q5'
CIRCUIT_ID = '1805172331643322369'

qcis_code = '''
  ????
  ????
  ????
'''.strip()
print(qcis_code)


data = {
  'inputCode': qcis_code,
  'quantumComputerId': '3',
  'quantumLanguageId': '1750056099560656897',
  'source': 'Composer',
  'name': CIRCUIT_NAME,
  'experimentDetailId': CIRCUIT_ID,
}

print(f'[POST] {API_URL}')
resp = R.post(API_URL, json=data, headers=HEADERS)
assert resp.ok, breakpoint()
resp_data = resp.json()
assert resp_data and resp_data.get('code') == 200, breakpoint()
data = resp_data.get('data')
assert data, breakpoint()
print(data)
