import logging
import os
import tempfile

import nltk
from flask import Flask, jsonify, send_file
from google.cloud import storage
from wordcloud import WordCloud

nltk.data.path.append("/tmp")
nltk.download('stopwords', download_dir="/tmp")
nltk.download('punkt', download_dir="/tmp")

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words('english'))

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Configure these environment variables
CLOUD_STORAGE_BUCKET_SOURCE = os.environ.get('CLOUD_STORAGE_BUCKET_SOURCE')


@app.route('/')
def index():
    return "welcome to file processing app"


@app.route('/generate_word_cloud', methods=['GET'])
def generate_word_cloud():
    word_frequency = {}
    try:
        # Initializing GCP storage client
        gcp_storage = storage.Client()

        # Fetching the blobs object for the desired bucket
        blobs = gcp_storage.list_blobs(CLOUD_STORAGE_BUCKET_SOURCE)

        files = []
        for blob in blobs:
            files.append(blob.name)
            downloaded_blob = blob.download_as_string()
            downloaded_blob = downloaded_blob.decode("utf-8")
            print(downloaded_blob)

            text_tokens = word_tokenize(downloaded_blob)

            for word in text_tokens:
                if word.isalpha() and word not in stop_words and (
                        word[0].isupper() or word.isupper()) and word.lower() not in stop_words:
                    if word not in word_frequency:
                        word_frequency[word] = 0
                    word_frequency[word] += 1

        app.logger.info("Files retrieved from the bucket: {} are: {}".format(CLOUD_STORAGE_BUCKET_SOURCE, files))
        app.logger.info(
            "Word frequency created for all the files in the bucket: {} \n {}".format(CLOUD_STORAGE_BUCKET_SOURCE,
                                                                                      word_frequency))

        word_cloud = WordCloud(background_color="white", width=1000, height=1000, relative_scaling=0.5,
                               normalize_plurals=False).generate_from_frequencies(word_frequency)

        with tempfile.NamedTemporaryFile() as temp:
            word_cloud.to_file(temp.name + ".png")

            return send_file(temp.name + ".png", attachment_filename='word_cloud.png')

    except Exception as e:
        app.logger.error(e)
        return jsonify(message="An error occurred while generating word cloud for the file", error=str(e)), 409


# def fetch_and_upload_data(bucket, object_name):
#     bucket = gcs.bucket(bucket)
#     blob = bucket.blob(object_name)
#
#     filename = 'tmp_' + object_name
#     blob.download_to_filename(filename)
#
#     app.logger.info("downloaded file {}".format(filename))
#
#     out_bucket = gcs.bucket(CLOUD_STORAGE_BUCKET_DEST)
#     out_blob = out_bucket.blob(filename)
#     out_blob.upload_from_filename(filename)
#
#     if os.path.exists(filename):
#         os.remove(filename)
#
#     app.logger.info("uploaded file: {} to bucket {}".format(filename, CLOUD_STORAGE_BUCKET_DEST))
#     return jsonify({'message': 'uploaded file: {} to bucket {}'.format(filename, CLOUD_STORAGE_BUCKET_DEST)})


# @app.route('/process', methods=['POST'])
# def upload():
#     data = request.get_json()
#     app.logger.info(data)
#
#     message = data['message']
#     attributes = message['attributes']
#
#     bucket = attributes['bucketId']
#     object_name = attributes['objectId']
#
#     resp = fetch_and_upload_data(bucket, object_name)
#     return resp
#
#     return jsonify(message=data)

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
# [END gae_flex_storage_app]
