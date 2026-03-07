#!/usr/bin/env python3
"""
Training Data Migration Script

Migrates training data from old 11-grade system (A+, A-, B+, etc.) 
to new simplified 5-grade system (A, B, C, D, F).
"""

import boto3
import json
from typing import Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrainingDataMigrator:
    def __init__(self, bucket_name: str = 'tradeseeker-training-data'):
        self.s3_client = boto3.client('s3', region_name='ap-southeast-1')
        self.bucket_name = bucket_name
        
        # Grade mapping from old system to new system
        self.grade_mapping = {
            'A+': 'A',
            'A': 'A', 
            'A-': 'A',
            'B+': 'B',
            'B': 'B',
            'B-': 'B', 
            'C+': 'C',
            'C': 'C',
            'C-': 'C',
            'D': 'D',
            'F': 'F'
        }
    
    def migrate_training_data(self, dry_run: bool = True) -> Dict:
        """Migrate training data from old to new grade system"""
        
        logger.info(f"Starting training data migration (dry_run={dry_run})")
        logger.info(f"Bucket: {self.bucket_name}")
        
        try:
            # List all objects in the bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            migration_stats = {
                'total_files': 0,
                'migrated_files': 0,
                'skipped_files': 0,
                'error_files': 0,
                'grade_changes': {},
                'errors': []
            }
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    migration_stats['total_files'] += 1
                    
                    # Skip if not a JSON file or in root directory
                    if not key.endswith('.json') or '/' not in key:
                        migration_stats['skipped_files'] += 1
                        continue
                    
                    # Extract current grade from folder structure
                    parts = key.split('/')
                    if len(parts) < 3:  # Need at least training-data/grade/file.json
                        migration_stats['skipped_files'] += 1
                        continue
                    
                    # Skip the training-data prefix and get the actual grade
                    if parts[0] == 'training-data':
                        old_grade = parts[1]  # The grade is the second part
                        filename = parts[2]   # The filename is the third part
                    else:
                        old_grade = parts[0]  # Direct grade folder
                        filename = parts[1]   # The filename is the second part
                    
                    # Check if grade needs migration
                    if old_grade not in self.grade_mapping:
                        logger.warning(f"Unknown grade '{old_grade}' in {key}")
                        migration_stats['skipped_files'] += 1
                        continue
                    
                    new_grade = self.grade_mapping[old_grade]
                    
                    # Skip if already in correct grade
                    if old_grade == new_grade:
                        migration_stats['skipped_files'] += 1
                        continue
                    
                    # Track grade changes
                    change_key = f"{old_grade} → {new_grade}"
                    migration_stats['grade_changes'][change_key] = migration_stats['grade_changes'].get(change_key, 0) + 1
                    
                    if not dry_run:
                        try:
                            # Download the file
                            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                            file_content = response['Body'].read()
                            
                            # Create new key with updated grade (keep training-data prefix)
                            new_key = f"training-data/{new_grade}/{filename}"
                            
                            # Upload to new location
                            self.s3_client.put_object(
                                Bucket=self.bucket_name,
                                Key=new_key,
                                Body=file_content,
                                ContentType='application/json'
                            )
                            
                            # Delete old file
                            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                            
                            logger.info(f"Migrated: {key} → {new_key}")
                            migration_stats['migrated_files'] += 1
                            
                        except Exception as e:
                            error_msg = f"Error migrating {key}: {str(e)}"
                            logger.error(error_msg)
                            migration_stats['errors'].append(error_msg)
                            migration_stats['error_files'] += 1
                    else:
                        # Dry run - just log what would be done
                        new_key = f"training-data/{new_grade}/{filename}"
                        logger.info(f"Would migrate: {key} → {new_key}")
                        migration_stats['migrated_files'] += 1
            
            return migration_stats
            
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            return {'error': str(e)}


def main():
    """Main function to run migration"""
    
    print("🔄 Training Data Migration Tool")
    print("=" * 40)
    print()
    print("This tool migrates training data from the old 11-grade system")
    print("(A+, A-, B+, B-, C+, C-, D, F) to the new 5-grade system (A, B, C, D, F)")
    print()
    
    migrator = TrainingDataMigrator()
    
    # First run a dry run to show what would be migrated
    print("🔍 Running dry run to analyze current data...")
    dry_run_results = migrator.migrate_training_data(dry_run=True)
    
    if 'error' in dry_run_results:
        print(f"❌ Error: {dry_run_results['error']}")
        return
    
    # Show dry run results
    print(f"📊 Migration Analysis:")
    print(f"   Total files: {dry_run_results['total_files']}")
    print(f"   Files to migrate: {dry_run_results['migrated_files']}")
    print(f"   Files to skip: {dry_run_results['skipped_files']}")
    print()
    
    if dry_run_results['migrated_files'] == 0:
        print("✅ No migration needed - all training data already uses the new grade system")
        return
    
    print("📈 Grade Changes:")
    for change, count in dry_run_results['grade_changes'].items():
        print(f"   {change}: {count} files")
    print()
    
    # Ask for confirmation
    response = input("Proceed with migration? This will move files in S3. (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Migration cancelled")
        return
    
    # Run actual migration
    print("🚀 Running migration...")
    results = migrator.migrate_training_data(dry_run=False)
    
    if 'error' in results:
        print(f"❌ Migration failed: {results['error']}")
        return
    
    # Show final results
    print()
    print("✅ Migration completed!")
    print(f"   Files migrated: {results['migrated_files']}")
    print(f"   Files skipped: {results['skipped_files']}")
    print(f"   Errors: {results['error_files']}")
    
    if results['errors']:
        print()
        print("⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   {error}")
    
    print()
    print("🎯 Next steps:")
    print("   1. Run 'make train-check' to verify the migration")
    print("   2. Run 'make train' to calibrate with the updated data")


if __name__ == "__main__":
    main()