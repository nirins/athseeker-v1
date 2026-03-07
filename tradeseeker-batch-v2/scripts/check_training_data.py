#!/usr/bin/env python3
"""
Check Training Data Status

Quick script to check the current status of training data in S3 bucket.
"""

import boto3
from collections import defaultdict
import json

def check_training_data_status(bucket_name: str = 'tradeseeker-training-data'):
    """Check training data status in S3 bucket"""
    
    try:
        s3_client = boto3.client('s3', region_name='ap-southeast-1')
        
        print(f"🔍 Checking training data in bucket: {bucket_name}")
        print("=" * 50)
        
        # List all objects in the bucket
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        grade_counts = defaultdict(int)
        total_files = 0
        sample_files = defaultdict(list)
        
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                key = obj['Key']
                
                # Skip if not a JSON file
                if not key.endswith('.json'):
                    continue
                
                # Extract grade from folder structure
                parts = key.split('/')
                if len(parts) >= 3 and parts[0] == 'training-data':
                    grade = parts[1]  # Second part is the grade folder
                elif len(parts) >= 2:
                    grade = parts[0]  # First part is the grade folder (legacy format)
                else:
                    continue
                
                grade_counts[grade] += 1
                total_files += 1
                
                # Keep sample files for each grade
                if len(sample_files[grade]) < 3:
                    sample_files[grade].append(key)
        
        if total_files == 0:
            print("❌ No training data found")
            print("   Start labeling charts in the web application to collect training data.")
            return
        
        print(f"📊 Training Data Summary:")
        print(f"   Total samples: {total_files}")
        print()
        
        print("📈 Grade Distribution:")
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_counts.get(grade, 0)
            percentage = (count / total_files * 100) if total_files > 0 else 0
            status = "✅" if count >= 20 else "⚠️" if count >= 10 else "❌"
            print(f"   Grade {grade}: {count:3d} samples ({percentage:5.1f}%) {status}")
        
        print()
        print("📄 Sample Files:")
        for grade in sorted(grade_counts.keys()):
            print(f"   Grade {grade}:")
            for file in sample_files[grade]:
                print(f"     - {file}")
        
        print()
        print("💡 Recommendations:")
        
        # Check if ready for calibration
        if total_files >= 50:
            print("   ✅ Ready for calibration (50+ samples)")
        else:
            needed = 50 - total_files
            print(f"   📊 Need {needed} more samples for reliable calibration")
        
        # Check grade balance
        min_samples = min(grade_counts.values()) if grade_counts else 0
        max_samples = max(grade_counts.values()) if grade_counts else 0
        
        if max_samples > min_samples * 3:
            print("   ⚖️  Grade distribution is unbalanced - collect more samples for underrepresented grades")
        
        # Check minimum per grade
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_counts.get(grade, 0)
            if count < 10:
                print(f"   📈 Need more Grade {grade} samples (current: {count}, recommended: 20+)")
        
        print()
        print("🚀 Next Steps:")
        if total_files >= 100:
            print("   1. Run calibration: python calibrate_beauty_model.py")
            print("   2. Review results and apply optimized weights")
            print("   3. Deploy updated model: make batch")
        else:
            print("   1. Continue labeling charts in the web application")
            print("   2. Aim for balanced distribution across all grades")
            print("   3. Return here when you have 100+ samples")
        
    except Exception as e:
        print(f"❌ Error checking training data: {str(e)}")
        print("   Make sure AWS credentials are configured and S3 bucket exists.")

if __name__ == "__main__":
    check_training_data_status()