#!/usr/bin/env python3
"""
Transfer Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf to S3
17.9GB file upload with multipart transfer
"""

import os
import boto3
from pathlib import Path
import sys
from tqdm import tqdm

def transfer_to_s3():
    """Transfer Qwen3.5 model to S3"""
    
    # Configuration
    source_file = Path("E:/TELECHARGEMENT-18-20AOUT/Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf")
    bucket_name = "deepseek-models-326095712935"
    s3_key = "models/qwen/Qwen3.5-9B-DeepSeek-V4-Flash-BF16.gguf"
    
    print(f"🎯 S3 Transfer: Qwen3.5")
    print(f"📁 Source: {source_file}")
    print(f"🪣 Bucket: {bucket_name}")
    print(f"🔑 S3 Key: {s3_key}")
    
    # Verify source file exists
    if not source_file.exists():
        print(f"❌ Source file not found: {source_file}")
        return False
    
    # Get file size
    file_size = source_file.stat().st_size
    print(f"📊 File size: {file_size / (1024**3):.1f} GB")
    
    # Initialize S3 client
    try:
        s3_client = boto3.client('s3')
        print("✅ S3 client initialized")
    except Exception as e:
        print(f"❌ S3 client error: {e}")
        return False
    
    # Check if bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✅ Bucket accessible: {bucket_name}")
    except Exception as e:
        print(f"❌ Bucket error: {e}")
        return False
    
    # Check if file already exists in S3
    try:
        s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        print(f"⚠️  File already exists in S3")
        response = input("Overwrite? (y/N): ").lower()
        if response != 'y':
            print("❌ Transfer cancelled")
            return False
    except:
        print("✅ File not in S3, proceeding with upload")
    
    try:
        # Use multipart upload for large files
        print("🚀 Starting multipart upload...")
        
        # Create multipart upload
        response = s3_client.create_multipart_upload(
            Bucket=bucket_name,
            Key=s3_key,
            StorageClass='STANDARD'
        )
        upload_id = response['UploadId']
        
        # Calculate part size (8MB chunks)
        part_size = 8 * 1024 * 1024
        parts = []
        
        # Upload parts
        with open(source_file, 'rb') as f:
            part_number = 1
            while True:
                data = f.read(part_size)
                if not data:
                    break
                
                print(f"📤 Uploading part {part_number}...")
                
                # Upload part
                response = s3_client.upload_part(
                    Bucket=bucket_name,
                    Key=s3_key,
                    PartNumber=part_number,
                    UploadId=upload_id,
                    Body=data
                )
                
                parts.append({
                    'ETag': response['ETag'],
                    'PartNumber': part_number
                })
                
                part_number += 1
        
        # Complete multipart upload
        print("🔗 Completing multipart upload...")
        s3_client.complete_multipart_upload(
            Bucket=bucket_name,
            Key=s3_key,
            UploadId=upload_id,
            MultipartUpload={'Parts': parts}
        )
        
        print("✅ Transfer completed successfully!")
        print(f"🌐 S3 URL: s3://{bucket_name}/{s3_key}")
        
        return True
        
    except Exception as e:
        print(f"❌ Transfer failed: {e}")
        
        # Abort multipart upload on failure
        try:
            s3_client.abort_multipart_upload(
                Bucket=bucket_name,
                Key=s3_key,
                UploadId=upload_id
            )
            print("🧹 Cleaned up incomplete upload")
        except:
            pass
        
        return False

if __name__ == "__main__":
    print("🚀 Qwen3.5 S3 Transfer")
    print("=" * 50)
    
    success = transfer_to_s3()
    
    if success:
        print("\n✅ SUCCESS: Ready for AWS deployment!")
        print("🎯 Next step: Deploy to c5.4xlarge instance")
    else:
        print("\n❌ FAILED: Transfer incomplete")
        sys.exit(1)
