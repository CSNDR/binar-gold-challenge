from flask import Flask, request, jsonify
import re
import pandas as pd
from unidecode import unidecode
import sqlite3
import time
from flasgger import Swagger, LazyString, LazyJSONEncoder, swag_from



app =  Flask(__name__)
app.json_encoder = LazyJSONEncoder

swagger_template = dict(
info = {
    'title': LazyString(lambda: 'Binar Gold Challenge'),
    'version': LazyString(lambda: '1'),
    'description': LazyString(lambda: 'API CLEANSING TEXT'),
    },
    host = LazyString(lambda: request.host)
)

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'docs',
            "route": '/docs.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs/"
}

swagger = Swagger(app, template=swagger_template,             
                  config=swagger_config)

def _remove_punct(s):
    return re.sub(r"[^\w\d\s]+", "",s)


def remove_ascii2(s):
    return re.sub(r"\\x[A-Za-z0-9./]+","",unidecode(s))

def clean_text(s):
    s = s.strip().replace(r'\n'," ")
    s = remove_ascii2(s)
    s = s.strip()
    s = re.sub(r"[^\w\d\s]+"," ",s)
    return s  

@swag_from("swagger_config_post.yml", methods=['POST'])
@app.route("/clean_text/v1", methods=['POST'])
def remove_punct_post():
    s = request.get_json()
    s = s['text']
    line = s.strip()
    line = line.replace('\n','')
    line = bytes(s, 'utf-8').decode('utf-8', 'ignore')
    clean_text = _remove_punct(line)
    
    conn = sqlite3.connect("clean_text.db")
    sql = f"INSERT INTO input_user (dirty_text,clean_text) VALUES ('{s}', '{clean_text}')"
    print(sql)
    conn.execute(sql)
    conn.commit()
    conn.close()    

    dict_result = { 
        "result": clean_text
    }
    return jsonify(dict_result)


@swag_from("swagger_config_file.yml", methods=['POST'])
@app.route("/upload_csv/v1", methods=['POST'])
def post_file():
    file = request.files["file"]
    start = time.time()
    df = pd.read_csv(file, encoding='ISO-8859-1')
    df['Clean_tweet'] = df.Tweet.apply(clean_text)
    
    conn = sqlite3.connect("tweet_file.db")
    df.to_sql('tweet', con=conn, index=False, if_exists='append')
    conn.close() 
    end = time.time()

    dict_result = {
        "result": "file berhasil di upload ke db",
        "total execution time": end - start}

    return jsonify(dict_result)


if __name__ == "__main__":
    app.run(port=1234, debug=True)