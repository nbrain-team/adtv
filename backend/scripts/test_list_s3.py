import os
from dotenv import load_dotenv
import boto3

if __name__ == "__main__":
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', 'adtv-backend.env'))
    s3 = boto3.client('s3', region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-2'))
    bucket = os.getenv('PODIO_S3_BUCKET', 'podio-export')
    prefix = os.getenv('PODIO_S3_PREFIX', 'output/')
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=5)
    contents = [c['Key'] for c in resp.get('Contents', [])]
    print({'bucket': bucket, 'prefix': prefix, 'sampleKeys': contents}) 