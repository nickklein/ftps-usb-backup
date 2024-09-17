import boto3
import os

class S3Uploader:
    def __init__(self, access_key, secret_key, bucket_name, key_prefix='', region_name='us-east-1'):
        self.bucket_name = bucket_name
        self.key_prefix = key_prefix
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region_name
        )

    def upload(self, file_path):
        try:
            filename = os.path.basename(file_path)
            s3_key = os.path.join(self.key_prefix, filename) if self.key_prefix else filename
            self.s3_client.upload_file(file_path, self.bucket_name, s3_key)
            print(f"Uploaded {filename} to S3 bucket {self.bucket_name}")
        except Exception as e:
            print(f"S3 upload failed: {e}")
