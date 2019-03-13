import argparse
import os
import sys
import glob
import traceback
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from bs4 import BeautifulSoup


parser = argparse.ArgumentParser()
parser.add_argument('folder', help='Folder with AQUAINT files')
parser.add_argument('--index', '-i', default='aquaint', help='elastic index')
args = parser.parse_args()

if not os.path.isdir(args.folder):
    print("source folder specified invalid")
    sys.exit(1)

es = Elasticsearch(['127.0.0.1:9200'])

files = []
for filename in glob.iglob(args.folder + '/*/', recursive=True):
    if os.path.isfile(filename):
        files.append(filename)

for file in files:
    print(file)
    with open(file) as f:
        content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        docs = soup.find_all('doc')
        actions = []
        for doc in docs:
            try:
                # only process news stories
                if doc.find('doctype') != None and doc.find('doctype').string.strip() != "NEWS STORY":
                    continue

                body = ""
                if doc.find('text').string != None:
                    body = doc.find('text').string.strip()
                if len(doc.find_all('p')) > 0:
                    body = "".join(['<p>{}</p>'.format(x.string) for x in doc.find_all('p')]),
                actions.append({
                    '_index': args.index,
                    '_type': '_doc',
                    '_source': {
                        'docno': doc.find('docno').string.strip(),
                        # parse time and let Elastic know
                        'datetime': doc.find('date_time').string.strip() + ":00",
                        'headline': doc.find('headline').string.strip(),
                        'body': body
                    }
                })
            except Exception as e:
                    print(str(e))
                    print(traceback.format_exc())
        helpers.bulk(es, actions)