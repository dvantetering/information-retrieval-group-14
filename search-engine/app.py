from flask import Flask, render_template, request
from logging.handlers import RotatingFileHandler
from elasticsearch import Elasticsearch
from datetime import datetime
import logging

app = Flask(__name__)
app.debug = True
es = Elasticsearch('127.0.0.1', port=9200)
res = {}
relevant_ids = []
search_term = ""



@app.route('/')
def home():
    return render_template("search.html")


@app.route('/search/results', methods=['POST'])
def search_request():
    global search_term
    if request.values.get('docid'):
        id = request.values.get('docid')
        checked = request.values.get('checked')
        if checked=='true':
            relevant_ids.append(id)
            app.logger.info(str(datetime.now()) + ": " + "Marked relevant: " + id)
        else:
            relevant_ids.remove(id)
            app.logger.info(str(datetime.now()) + ": " + "Marked irrelevant: " + id)
        print('relevant ids: ', relevant_ids)
    else:
        search_term = request.form["input"]
        global res
        res = es.search(
            index="aquaint",
            size=1000,
            body={
                "query": {
                    "multi_match" : {
                        "query": search_term,
                        "fields": [
                            "headline",
                            "body"
                     ]
                 }
             }
        }

        )
        app.logger.info(str(datetime.now()) + ": Entered query: " + search_term)
    # res = es.search(index="test-index", body={"query": {"match_all": {}}})
    print("Got %d Hits:" % res['hits']['total'])
    return render_template('results.html', res=res, search_term=search_term, relevant_ids=relevant_ids )


@app.route('/view/<docid>')
def view_result(docid):
    res = es.search(
        index="aquaint",
        size=1,
        body={
            "query": {
                "match": {
                    "_id": docid
                }
            }
        }
    )
    result = res['hits']['hits'][0]
    if type(result['_source']['body']) is list:
        result['_source']['body'] = " ".join(str(x) for x in result['_source']['body'])

    result['_source']['body'] = result['_source']['body'].replace('<p>', '')
    result['_source']['body'] = result['_source']['body'].replace('</p>', '')
    app.logger.info(str(datetime.now()) + ": Clicked docid: " + docid)
    return render_template('view.html', res=result)


if __name__ == '__main__':
    app.secret_key = 'mysecret'
    handler = RotatingFileHandler('username.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000)