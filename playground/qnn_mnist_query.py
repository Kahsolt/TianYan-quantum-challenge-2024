#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/24

# 中电信量子的官方示例: 手写数字识别，让我们看看他这个模型的准确率 :)
# https://qc.zdxlz.com/solution/digitalRecognition?lang=zh

import os
import json
import random
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
from re import compile as Regex
from time import sleep
from datetime import datetime
from argparse import ArgumentParser
from typing import List, Tuple
from traceback import print_exc

import numpy as np
from numpy import ndarray
from tqdm import tqdm
import requests as R

BASE_PATH = Path(__file__).parent
DATA_FILE = BASE_PATH / 'mnist-3k.npz'    # the first 3k samples from torchvision.datasets.MNIST testset
RECORD_FILE = BASE_PATH / f'{Path(__file__).stem}.json'

AUTH_TOKEN = os.getenv('AUTH_TOKEN')
API_URL = 'https://qc.zdxlz.com/qccp-quantum/imageIdentify'
SLEEP_TIME = 8 * 2
R_ENCODER = Regex('RY Q0 (-?[\d\.]+) RY Q1 (-?[\d\.]+) RY Q2 (-?[\d\.]+) RY Q3 (-?[\d\.]+) RY Q4 (-?[\d\.]+) ')
EMPTY_IM = np.zeros([28, 28], dtype=np.uint8)
BATCH_SIZE = 3
RESIZE = (280, 280)
REQ_DATA_TMPL = {
  'images': [
    str,      # base64 编码 280*280 尺寸的 png 图像
  ]
}
RESP_DATA_TMPL = {
  "code": int,
  "msg": {
    "CN": str,
    "EN": str,
  },
  "data": {
    "msg": str,
    "recog_objs": [str],    # 识别结果
    "qcis_codes": [str],    # 线路
  }
}
HEADERS = {
  'Content-Type': 'application/json',
  'Accept': 'application/json, text/plain, */*',
  'Accept-Encoding': 'gzip, deflate, br, zstd',
  'Origin': 'https://qc.zdxlz.com',
  'Referer': 'https://qc.zdxlz.com/solution/digitalRecognition?lang=zh',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
  'Authorization': AUTH_TOKEN,
  'apiCode': 'imageIdentifyHeard',
}

http = R.session()


def im_to_base64(im:ndarray):
  im = np.stack([EMPTY_IM, EMPTY_IM, EMPTY_IM, im], axis=-1)    # data is at alpha channel
  img = Image.fromarray(im, mode='RGBA')
  img = img.resize(RESIZE, resample=Image.Resampling.NEAREST)
  buf = BytesIO()
  img.save(buf, format='PNG')
  bdata = buf.getvalue()
  base64_str = base64.b64encode(bdata)
  return base64_str.decode()


def parse_encoder_data(qcis_code:str) -> List[float]:
  qcis_code = qcis_code.replace('\n', ' ')
  try:
    m = R_ENCODER.findall(qcis_code)[0]
  except:
    print('>> qcis_code:', qcis_code[:50] + '......')
    print('>> pattern not found!')
    breakpoint()
  return [round(float(e), 3) for e in m]


def query_batch(batch:List[Tuple[int, ndarray, int]]) -> List[Tuple[int, List[float]]]:
  post_data = {
    'images': [
      im_to_base64(x) for i, x, y in batch
    ]
  }
  headers_var = {
    # fmt: '6/24/2024, 1:02:10 AM'
    'requestTime': datetime.strftime(datetime.now(), '%m/%d/%Y, %I:%M:%S %p'),
  }
  resp = http.post(API_URL, json=post_data, headers=HEADERS | headers_var)
  if not resp.ok:
    raise RuntimeError('not resp.ok')
  resp_data = resp.json()
  if 'data' not in resp_data or not resp_data['data']:
    raise RuntimeError('resp.data is null')
  recog_objs: List[str] = resp_data['data']['recog_objs']
  recog_nums = [int(x) if x.isdigit() else None for x in recog_objs]
  qcis_codes: List[str] = resp_data['data']['qcis_codes']
  encoder_data = [parse_encoder_data(it) if it else None for it in qcis_codes]
  return zip(recog_nums, encoder_data)


def run():
  ''' Data '''
  data = np.load(DATA_FILE)
  X, Y = data['X'], data['Y']

  ''' Record (load) '''
  if RECORD_FILE.exists():
    with open(RECORD_FILE, 'r', encoding='utf-8') as fh:
      db = json.load(fh)
    inputs = db['inputs']
    cmat = np.asarray(db['cmat'], dtype=np.int32)
  else:
    inputs = [None] * len(Y)
    cmat = np.zeros([10, 10], dtype=np.int32)

  ''' Data (filter-completed & batched) '''
  samples = []
  for i, (x, y) in enumerate(zip(X, Y)):
    if inputs[i]: continue
    samples.append((i, x, y))
  print(f'>> n_samples: {len(samples)}')
  batches = []
  while len(samples):
    batch = samples[:BATCH_SIZE]
    samples = samples[BATCH_SIZE:]
    batches.append(batch)
  while len(batches[-1]) < BATCH_SIZE:
    batches[-1].append((-1, EMPTY_IM, -1))
  print(f'>> n_batches: {len(batches)}')

  ''' Go! '''
  for b, batch in enumerate(tqdm(batches)):
    try:
      for j, (y_pred, encoder_data) in enumerate(query_batch(batch)):
        i, x, y = batch[j]
        if i < 0: continue    # pad sample, dummy i == -1
        cmat[y, y_pred] += 1
        inputs[i] = encoder_data
    except:
      print_exc()
      print(f'>> Error at batch-{b}')

    if b % 10 == 0:
      db = {
        'inputs': inputs, 
        'cmat': cmat.tolist(),
      }
      with open(RECORD_FILE, 'w', encoding='utf-8') as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)

    sleep(random.randrange(SLEEP_TIME))

  ''' Record (save) '''
  db = {
    'inputs': inputs, 
    'cmat': cmat.tolist(),
  }
  with open(RECORD_FILE, 'w', encoding='utf-8') as fh:
    json.dump(db, fh, indent=2, ensure_ascii=False)


def analyze():
  assert RECORD_FILE.exists(), ">> need run query with -r first!"

  with open(RECORD_FILE, 'r', encoding='utf-8') as fh:
    db = json.load(fh)
  X = np.asarray(db['inputs'], dtype=np.float64)
  cmat = np.asarray(db['cmat'], dtype=np.int32)

  acc = np.diag(cmat).sum() / cmat.sum()
  print(f'>> acc: {acc:.3%}')   # 97.467%

  if not 'plot':
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.heatmap(cmat, cbar=True, annot=True, fmt='d')
    plt.suptitle('confusion matrix')
    plt.show()

  Y = np.load(DATA_FILE)['Y']

  if not 'plot pca(2)':
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    import matplotlib.pyplot as plt
    plt.scatter(X_pca[:, 0], X_pca[:, 1], c=Y, cmap='tab10')
    plt.suptitle('pca(encoder_data)')
    plt.show()

  if 'plot pca(3)':
    from sklearn.decomposition import PCA
    pca = PCA(n_components=3)
    X_pca = pca.fit_transform(X)

    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(X_pca[:, 0], X_pca[:, 1], X_pca[:, 2], c=Y, cmap='tab10')
    plt.suptitle('pca(encoder_data, dim=3)')
    plt.show()


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-r', action='store_true', help='run query')
  args = parser.parse_args()

  assert AUTH_TOKEN, '>> Error: need set AUTH_TOKEN envvar, you will find this in your browser under F11 mode :)'

  if args.r:
    print('>> Run [query]')
    run()
  else:
    print('>> Run [analyze]')
    analyze()
