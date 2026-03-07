#!/usr/bin/env python3
"""
Update Beauty Score Model Weights

This script updates the beauty score calculation weights in the breakout analyzer
based on calibration results from training data analysis.
"""

import json
import re
import os
from typing import Dict

def load_calibration_results(report_file: str = 'beauty_model_calibration_report.json') -> Dict:
    """Load calibration results from JSON report"""
    try:
        with open(report_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Calibration report not found: {report_file}")
        print("   Run calibrate_beauty_model.py first to generate the report.")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing calibration report: {e}")
        return {}

def update_breakout_analyzer_weights(weights: Dict, file_path: str) -> bool:
    """Update weights in breakout_analyzer.py file"""
    try:
        # Read the current file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Create the new weighted beauty score calculation
        new_calculation = f"""            # Weighted beauty score (0-100) - Updated from calibration
            beauty_score = (
                consolidation_score * {weights['consolidation']:.3f} +  # {weights['consolidation']*100:.1f}% - How well consolidated before breakout
                volume_score * {weights['volume']:.3f} +         # {weights['volume']*100:.1f}% - Volume surge on breakout
                momentum_score * {weights['momentum']:.3f} +       # {weights['momentum']*100:.1f}% - Momentum continuation after breakout
                green_candle_score * {weights['green_candle']:.3f} +   # {weights['green_candle']*100:.1f}% - Green candles around breakout
                gap_score * {weights['gap']:.3f}              # {weights['gap']*100:.1f}% - Gap up on breakout
            )"""
        
        # Pattern to match the existing weighted beauty score calculation
        pattern = r'(\s+# Weighted beauty score.*?\n\s+beauty_score = \(\s*\n(?:\s+.*?\n)*?\s+\))'
        
        # Replace the calculation
        updated_content = re.sub(pattern, new_calculation, content, flags=re.DOTALL)
        
        if updated_content == content:
            print(f"⚠️  No changes made to {file_path} - pattern not found")
            return False
        
        # Write the updated content back
        with open(file_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated weights in {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False

def backup_file(file_path: str) -> str:
    """Create a backup of the original file"""
    backup_path = f"{file_path}.backup"
    try:
        with open(file_path, 'r') as original:
            with open(backup_path, 'w') as backup:
                backup.write(original.read())
        print(f"📄 Backup created: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"⚠️  Failed to create backup: {e}")
        return ""

def main():
    """Main function to update beauty score weights"""
    print("🔧 Beauty Score Model Weight Update")
    print("=" * 40)
    
    # Load calibration results
    report = load_calibration_results()
    if not report:
        return
    
    optimization = report.get('optimization', {})
    if not optimization:
        print("❌ No optimization results found in calibration report")
        return
    
    optimized_weights = optimization.get('optimized_weights', {})
    current_weights = optimization.get('current_weights', {})
    
    if not optimized_weights:
        print("❌ No optimized weights found in calibration report")
        return
    
    # Show weight changes
    print("📊 Proposed Weight Changes:")
    print(f"{'Component':<15} {'Current':<8} {'Optimized':<10} {'Change':<8}")
    print("-" * 45)
    
    for component in current_weights:
        current = current_weights[component]
        optimized = optimized_weights.get(component, current)
        change = optimized - current
        arrow = "↗️" if change > 0 else "↘️" if change < 0 else "➡️"
        print(f"{component:<15} {current:<8.3f} {optimized:<10.3f} {change:+.3f} {arrow}")
    
    print()
    
    # Show performance improvement
    current_r2 = report['summary'].get('current_model_r2', 0)
    optimized_r2 = report['summary'].get('optimized_model_r2', 0)
    improvement = optimized_r2 - current_r2
    
    print(f"📈 Performance Improvement:")
    print(f"   Current R²: {current_r2:.3f}")
    print(f"   Optimized R²: {optimized_r2:.3f}")
    print(f"   Improvement: {improvement:+.3f}")
    print()
    
    # Ask for confirmation
    if improvement < 0.05:
        print("⚠️  Improvement is minimal (<0.05). Consider collecting more training data.")
        response = input("Continue with update anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Update cancelled")
            return
    else:
        response = input("Apply these weight changes? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Update cancelled")
            return
    
    # Files to update
    files_to_update = [
        '../lambdas/downloader/breakout_analyzer.py',
        '../lambdas/downloader/package/breakout_analyzer.py'
    ]
    
    updated_files = []
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            # Create backup
            backup_path = backup_file(file_path)
            
            # Update the file
            if update_breakout_analyzer_weights(optimized_weights, file_path):
                updated_files.append(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    if updated_files:
        print()
        print("✅ Weight update completed!")
        print(f"   Updated {len(updated_files)} files")
        print("   Backups created with .backup extension")
        print()
        print("🚀 Next steps:")
        print("   1. Review the changes in the updated files")
        print("   2. Run 'make batch' to deploy the updated model")
        print("   3. Monitor beauty score performance with new weights")
    else:
        print("❌ No files were updated")

if __name__ == "__main__":
    main()