import os
from flask import Flask, request, jsonify
import requests
from google.cloud import secretmanager, storage, pubsub_v1
import json
from datetime import datetime
import logging
import concurrent.futures

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("wasde-integration")

# Initialize clients outside the request context for efficiency
secret_client = secretmanager.SecretManagerServiceClient()
storage_client = storage.Client()
publisher_client = pubsub_v1.PublisherClient()

# Configuration
# Use environment variable for GCP_PROJECT, defaulting to 'final-cb-app' if not set
PROJECT_ID = os.environ.get('GCP_PROJECT', 'final-cb-app')
SECRET_NAME = f"projects/{PROJECT_ID}/secrets/nasdaq-wasde-api-key/versions/latest"
RAW_DATA_BUCKET_NAME = f'{PROJECT_ID}-financial-market-raw-data'
INGESTION_TOPIC_NAME = f"projects/{PROJECT_ID}/topics/financial-data-ingestion-topic"

def load_feeds():
    """Loads the list of feeds from the feeds.json file."""
    with open('feeds.json', 'r') as f:
        return json.load(f)

FEEDS = load_feeds()

def process_feed(feed: str, api_key: str, bucket) -> str:
    """
    Processes a single data feed: fetches from API, uploads to GCS, and publishes to Pub/Sub.
    Returns the feed name on success or raises an exception on failure.
    """
    url = f"https://data.nasdaq.com/api/v3/datasets/{feed}.json"
    log.info(f"Starting processing for feed: {feed}")
    
    # Make API request
    r = requests.get(url, params={'api_key': api_key, 'start_date': '2020-01-01'})
    r.raise_for_status()
    
    # Store raw data in GCS
    blob_name = f"wasde/{feed.replace('/', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(r.text, content_type="application/json")
    log.info(f"Uploaded {blob_name} to {RAW_DATA_BUCKET_NAME}")
    
    # Publish message to Pub/Sub
    message_data = {
        "source": "wasde",
        "feed": feed,
        "gcs_path": f"gs://{RAW_DATA_BUCKET_NAME}/{blob_name}",
        "timestamp": datetime.now().isoformat()
    }
    future = publisher_client.publish(
        INGESTION_TOPIC_NAME,
        data=json.dumps(message_data).encode("utf-8"),
        origin="wasde-ingestion",
        feed_name=feed.replace('/', '_')
    )
    future.result()  # Wait for the publish call to complete
    log.info(f"Published message for feed {feed}")
    return feed

@app.route('/wasde', methods=['POST'])
def fetch_wasde_data():
    """
    Fetches WASDE data from NASDAQ API, stores it in GCS, and publishes a message to Pub/Sub.
    This function is designed to be triggered by an HTTP POST request to the /wasde endpoint.
    """
    try:
        # Retrieve API key from Secret Manager
        api_key_response = secret_client.access_secret_version(request={"name": SECRET_NAME})
        api_key = api_key_response.payload.data.decode("UTF-8")

        bucket = storage_client.bucket(RAW_DATA_BUCKET_NAME)

        success_count = 0
        failed_feeds = []
        # Use a ThreadPoolExecutor to process feeds in parallel, making the overall request much faster.
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Map the process_feed function to each feed in the FEEDS list
            future_to_feed = {executor.submit(process_feed, feed, api_key, bucket): feed for feed in FEEDS}
            for future in concurrent.futures.as_completed(future_to_feed):
                feed = future_to_feed[future]
                try:
                    future.result()
                    success_count += 1
                except Exception as exc:
                    log.error(f'{feed} generated an exception: {exc}')
                    failed_feeds.append(feed)

        message = f"Processed {success_count}/{len(FEEDS)} feeds."
        if failed_feeds:
            message += f" Failures: {', '.join(failed_feeds)}"
        return jsonify({"status": "partial_success" if failed_feeds else "success", "message": message}), 200

    except requests.exceptions.RequestException as e:
        log.error(f"HTTP Request failed: {e}")
        return jsonify({"status": "error", "message": f"External API request failed: {e}"}), 500
    except Exception as e:
        log.exception(f"An unexpected error occurred: {e}")
        return jsonify({"status": "error", "message": f"An internal error occurred: {e}"}), 500

if __name__ == '__main__':
    # This is used when running locally. Gunicorn is used when running on Cloud Run.
    # Cloud Run will automatically set the PORT environment variable.
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
