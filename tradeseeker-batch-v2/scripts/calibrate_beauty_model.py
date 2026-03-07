#!/usr/bin/env python3
"""
Beauty Score Model Calibration Script

This script analyzes manually labeled training data to calibrate and improve
the automated beauty score calculation model.
"""

import boto3
import json
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Tuple, Optional
from statistics import mean, stdev
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BeautyModelCalibrator:
    def __init__(self, bucket_name: str = 'tradeseeker-training-data'):
        self.s3_client = boto3.client('s3', region_name='ap-southeast-1')
        self.bucket_name = bucket_name
        self.training_data = []
        self.grade_to_score = {'A': 90, 'B': 75, 'C': 60, 'D': 45, 'F': 25}
        
    def load_training_data(self) -> List[Dict]:
        """Load all training data from S3 bucket"""
        logger.info(f"Loading training data from S3 bucket: {self.bucket_name}")
        
        try:
            # List all objects in the training data bucket
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            training_data = []
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Skip if not a JSON file
                    if not key.endswith('.json'):
                        continue
                    
                    # Extract grade from folder structure: training-data/{grade}/{symbol}-{timestamp}.json
                    parts = key.split('/')
                    if len(parts) >= 3 and parts[0] == 'training-data':
                        grade = parts[1]  # Second part is the grade folder
                    elif len(parts) >= 2:
                        grade = parts[0]  # First part is the grade folder (legacy format)
                    else:
                        continue
                    
                    try:
                        # Download and parse the training data
                        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                        data = json.loads(response['Body'].read().decode('utf-8'))
                        
                        # Add grade and metadata
                        data['manual_grade'] = grade
                        data['s3_key'] = key
                        data['symbol'] = data.get('symbol', 'UNKNOWN')
                        
                        training_data.append(data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load {key}: {str(e)}")
                        continue
            
            logger.info(f"Loaded {len(training_data)} training samples")
            self.training_data = training_data
            return training_data
            
        except Exception as e:
            logger.error(f"Error loading training data: {str(e)}")
            return []
    
    def calculate_beauty_scores(self, stock_data: Dict) -> Dict:
        """Calculate beauty scores for a stock using current algorithm"""
        try:
            # Training data has structure: {stockData: {prices: [...], emas: {...}}}
            if 'stockData' in stock_data:
                actual_stock_data = stock_data['stockData']
            else:
                actual_stock_data = stock_data
            
            prices = actual_stock_data.get('prices', [])
            if len(prices) < 10:
                return {'beauty_score': 0, 'reason': 'Insufficient data'}
            
            # Find the breakout point (assume it's around the middle for training data)
            breakout_idx = len(prices) // 2
            pre_breakout = prices[:breakout_idx]
            breakout_day = prices[breakout_idx]
            post_breakout = prices[breakout_idx:]
            
            # Calculate component scores using the same logic as the batch system
            consolidation_score = self._calculate_consolidation_score(pre_breakout)
            volume_score = self._calculate_volume_score(pre_breakout, breakout_day)
            momentum_score = self._calculate_momentum_score(pre_breakout, post_breakout)
            green_candle_score = self._calculate_green_candle_score(post_breakout)
            gap_score = self._calculate_gap_score(pre_breakout, breakout_day)
            
            # Current weighted beauty score
            beauty_score = (
                consolidation_score * 0.25 +
                volume_score * 0.20 +
                momentum_score * 0.25 +
                green_candle_score * 0.20 +
                gap_score * 0.10
            )
            
            return {
                'beauty_score': round(beauty_score, 1),
                'consolidation_score': round(consolidation_score, 1),
                'volume_score': round(volume_score, 1),
                'momentum_score': round(momentum_score, 1),
                'green_candle_score': round(green_candle_score, 1),
                'gap_score': round(gap_score, 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculating beauty score: {str(e)}")
            return {'beauty_score': 0, 'reason': f'Error: {str(e)}'}
    
    def analyze_correlations(self) -> Dict:
        """Analyze correlations between manual grades and calculated scores"""
        if not self.training_data:
            logger.error("No training data loaded")
            return {}
        
        logger.info("Analyzing correlations between manual grades and calculated scores...")
        
        # Prepare data for analysis
        analysis_data = []
        
        for sample in self.training_data:
            manual_grade = sample.get('manual_grade')
            if manual_grade not in self.grade_to_score:
                logger.warning(f"Unknown manual grade: {manual_grade}")
                continue
            
            # Calculate beauty scores for this sample
            beauty_scores = self.calculate_beauty_scores(sample)
            if beauty_scores.get('beauty_score', 0) == 0:
                logger.warning(f"Zero beauty score for {sample.get('symbol', 'unknown')}: {beauty_scores.get('reason', 'no reason')}")
                continue
            
            analysis_data.append({
                'symbol': sample.get('symbol'),
                'manual_grade': manual_grade,
                'manual_score': self.grade_to_score[manual_grade],
                'calculated_beauty_score': beauty_scores['beauty_score'],
                'consolidation_score': beauty_scores['consolidation_score'],
                'volume_score': beauty_scores['volume_score'],
                'momentum_score': beauty_scores['momentum_score'],
                'green_candle_score': beauty_scores['green_candle_score'],
                'gap_score': beauty_scores['gap_score']
            })
        
        logger.info(f"Valid analysis samples: {len(analysis_data)} out of {len(self.training_data)} total")
        
        if not analysis_data:
            logger.error("No valid analysis data found")
            return {}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(analysis_data)
        
        logger.info(f"Analyzing {len(df)} valid samples")
        
        # Calculate correlations
        correlations = {}
        score_columns = ['calculated_beauty_score', 'consolidation_score', 'volume_score', 
                        'momentum_score', 'green_candle_score', 'gap_score']
        
        for col in score_columns:
            correlation = df['manual_score'].corr(df[col])
            correlations[col] = correlation
        
        # Calculate current model performance
        mse = mean_squared_error(df['manual_score'], df['calculated_beauty_score'])
        r2 = r2_score(df['manual_score'], df['calculated_beauty_score'])
        
        # Grade distribution analysis
        grade_distribution = df['manual_grade'].value_counts().to_dict()
        
        # Average scores by grade
        avg_scores_by_grade = df.groupby('manual_grade')[score_columns].mean().to_dict()
        
        return {
            'sample_count': len(df),
            'correlations': correlations,
            'current_model_mse': mse,
            'current_model_r2': r2,
            'grade_distribution': grade_distribution,
            'avg_scores_by_grade': avg_scores_by_grade,
            'analysis_data': analysis_data
        }
    
    def optimize_weights(self, analysis_data: List[Dict]) -> Dict:
        """Use machine learning to find optimal weights for beauty score components"""
        logger.info("Optimizing component weights using linear regression...")
        
        if len(analysis_data) < 10:
            logger.error("Insufficient data for weight optimization")
            return {}
        
        # Prepare features (component scores) and target (manual scores)
        features = []
        targets = []
        
        for sample in analysis_data:
            features.append([
                sample['consolidation_score'],
                sample['volume_score'],
                sample['momentum_score'],
                sample['green_candle_score'],
                sample['gap_score']
            ])
            targets.append(sample['manual_score'])
        
        X = np.array(features)
        y = np.array(targets)
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Get optimized weights (normalize to sum to 1.0)
        raw_weights = model.coef_
        weight_sum = np.sum(np.abs(raw_weights))
        
        if weight_sum > 0:
            normalized_weights = np.abs(raw_weights) / weight_sum
        else:
            # Fallback to current weights
            normalized_weights = np.array([0.25, 0.20, 0.25, 0.20, 0.10])
        
        # Calculate optimized beauty scores
        optimized_scores = []
        for sample in analysis_data:
            optimized_score = (
                sample['consolidation_score'] * normalized_weights[0] +
                sample['volume_score'] * normalized_weights[1] +
                sample['momentum_score'] * normalized_weights[2] +
                sample['green_candle_score'] * normalized_weights[3] +
                sample['gap_score'] * normalized_weights[4]
            )
            optimized_scores.append(optimized_score)
        
        # Calculate performance metrics for optimized model
        optimized_mse = mean_squared_error(targets, optimized_scores)
        optimized_r2 = r2_score(targets, optimized_scores)
        
        return {
            'optimized_weights': {
                'consolidation': float(normalized_weights[0]),
                'volume': float(normalized_weights[1]),
                'momentum': float(normalized_weights[2]),
                'green_candle': float(normalized_weights[3]),
                'gap': float(normalized_weights[4])
            },
            'current_weights': {
                'consolidation': 0.25,
                'volume': 0.20,
                'momentum': 0.25,
                'green_candle': 0.20,
                'gap': 0.10
            },
            'optimized_mse': optimized_mse,
            'optimized_r2': optimized_r2,
            'model_intercept': float(model.intercept_)
        }
    
    def generate_calibration_report(self) -> Dict:
        """Generate comprehensive calibration report and create new model"""
        logger.info("Generating calibration report...")
        
        # Load training data
        self.load_training_data()
        
        if not self.training_data:
            return {'error': 'No training data available'}
        
        # Analyze correlations
        analysis_results = self.analyze_correlations()
        
        if not analysis_results:
            return {'error': 'Analysis failed'}
        
        # Optimize weights
        optimization_results = self.optimize_weights(analysis_results['analysis_data'])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(analysis_results, optimization_results)
        
        # Create new calibrated model if improvement is significant
        if optimization_results and optimization_results.get('optimized_r2', 0) > analysis_results.get('current_model_r2', 0) + 0.05:
            self._create_calibrated_model(optimization_results, analysis_results)
        
        return {
            'summary': {
                'total_samples': analysis_results['sample_count'],
                'grade_distribution': analysis_results['grade_distribution'],
                'current_model_r2': analysis_results['current_model_r2'],
                'optimized_model_r2': optimization_results.get('optimized_r2', 0)
            },
            'analysis': analysis_results,
            'optimization': optimization_results,
            'recommendations': recommendations
        }
    
    def _create_calibrated_model(self, optimization_results: Dict, analysis_results: Dict):
        """Create a new calibrated model with optimized weights"""
        try:
            from datetime import datetime
            
            # Prepare calibration metadata
            calibration_metadata = {
                'calibration_date': datetime.now().isoformat(),
                'training_samples': analysis_results['sample_count'],
                'model_r2': optimization_results.get('optimized_r2', 0),
                'improvement': optimization_results.get('optimized_r2', 0) - analysis_results.get('current_model_r2', 0)
            }
            
            # Save calibrated weights to file
            weights_file = os.path.join(os.path.dirname(__file__), 'calibrated_weights.json')
            calibration_data = {
                'model_name': 'calibrated',
                'model_version': '2.0',
                'optimized_weights': optimization_results['optimized_weights'],
                'calibration_date': calibration_metadata['calibration_date'],
                'training_samples': calibration_metadata['training_samples'],
                'model_r2': calibration_metadata['model_r2'],
                'improvement': calibration_metadata['improvement'],
                'current_weights': optimization_results['current_weights']
            }
            
            with open(weights_file, 'w') as f:
                json.dump(calibration_data, f, indent=2)
            
            logger.info(f"Created calibrated model with weights saved to {weights_file}")
            
        except Exception as e:
            logger.error(f"Error creating calibrated model: {str(e)}")
            raise
    
    def _generate_recommendations(self, analysis: Dict, optimization: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        # Check model performance
        current_r2 = analysis.get('current_model_r2', 0)
        optimized_r2 = optimization.get('optimized_r2', 0)
        
        if current_r2 < 0.5:
            recommendations.append("⚠️  Current model has low correlation with manual grades (R² < 0.5)")
        
        if optimized_r2 > current_r2 + 0.1:
            recommendations.append(f"✅ Optimized weights could improve model performance (R² {current_r2:.3f} → {optimized_r2:.3f})")
        
        # Check component correlations
        correlations = analysis.get('correlations', {})
        for component, correlation in correlations.items():
            if component != 'calculated_beauty_score' and abs(correlation) < 0.2:
                recommendations.append(f"⚠️  {component} has low correlation with manual grades ({correlation:.3f})")
        
        # Check sample distribution
        grade_dist = analysis.get('grade_distribution', {})
        total_samples = sum(grade_dist.values())
        
        for grade in ['A', 'B', 'C', 'D', 'F']:
            count = grade_dist.get(grade, 0)
            percentage = (count / total_samples * 100) if total_samples > 0 else 0
            
            if percentage < 10:
                recommendations.append(f"📊 Need more grade {grade} samples ({count} samples, {percentage:.1f}%)")
        
        # Weight change recommendations
        if optimization:
            current_weights = optimization.get('current_weights', {})
            optimized_weights = optimization.get('optimized_weights', {})
            
            for component in current_weights:
                current = current_weights[component]
                optimized = optimized_weights.get(component, current)
                change = abs(optimized - current)
                
                if change > 0.05:  # Significant change
                    direction = "increase" if optimized > current else "decrease"
                    recommendations.append(f"🔧 Consider {direction} {component} weight from {current:.2f} to {optimized:.2f}")
        
        return recommendations
    
    # Beauty score calculation methods (copied from breakout_analyzer.py)
    def _calculate_consolidation_score(self, pre_breakout: List[Dict]) -> float:
        """Score how well the price consolidated before breakout (0-100)"""
        if len(pre_breakout) < 5:
            return 50
        
        closes = [float(record['close']) for record in pre_breakout]
        avg_price = mean(closes)
        
        if avg_price == 0:
            return 50
        
        try:
            price_std = stdev(closes)
            coefficient_of_variation = (price_std / avg_price) * 100
            
            if coefficient_of_variation <= 5:
                score = 90 + (5 - coefficient_of_variation) * 2
            elif coefficient_of_variation <= 20:
                score = 90 - ((coefficient_of_variation - 5) * 6)
            else:
                score = max(0, 20 - (coefficient_of_variation - 20))
            
            return min(100, max(0, score))
        except:
            return 50
    
    def _calculate_volume_score(self, pre_breakout: List[Dict], breakout_day: Dict) -> float:
        """Score volume surge on breakout day (0-100)"""
        if len(pre_breakout) < 5:
            return 50
        
        pre_volumes = [float(record['volume']) for record in pre_breakout[-10:]]
        avg_volume = mean(pre_volumes) if pre_volumes else 1
        breakout_volume = float(breakout_day['volume'])
        
        if avg_volume == 0:
            return 50
        
        volume_ratio = breakout_volume / avg_volume
        
        if volume_ratio >= 3.0:
            return 100
        elif volume_ratio >= 2.0:
            return 80 + (volume_ratio - 2.0) * 20
        elif volume_ratio >= 1.5:
            return 60 + (volume_ratio - 1.5) * 40
        elif volume_ratio >= 1.0:
            return 40 + (volume_ratio - 1.0) * 40
        else:
            return max(0, volume_ratio * 40)
    
    def _calculate_momentum_score(self, pre_breakout: List[Dict], post_breakout: List[Dict]) -> float:
        """Score momentum continuation after breakout (0-100)"""
        if len(post_breakout) < 2:
            return 50
        
        breakout_price = float(post_breakout[0]['close'])
        momentum_points = 0
        total_days = min(5, len(post_breakout) - 1)
        
        for i in range(1, total_days + 1):
            if i < len(post_breakout):
                current_price = float(post_breakout[i]['close'])
                price_change = (current_price - breakout_price) / breakout_price * 100
                
                if price_change > 5:
                    momentum_points += 25
                elif price_change > 2:
                    momentum_points += 20
                elif price_change > 0:
                    momentum_points += 15
                elif price_change > -2:
                    momentum_points += 10
                else:
                    momentum_points += 0
        
        return min(100, (momentum_points / total_days) * 4)
    
    def _calculate_green_candle_score(self, post_breakout: List[Dict]) -> float:
        """Score percentage of green candles around breakout (0-100)"""
        if len(post_breakout) < 2:
            return 50
        
        green_candles = 0
        total_candles = min(5, len(post_breakout))
        
        for record in post_breakout[:total_candles]:
            open_price = float(record['open'])
            close_price = float(record['close'])
            
            if close_price > open_price:
                green_candles += 1
        
        return (green_candles / total_candles) * 100
    
    def _calculate_gap_score(self, pre_breakout: List[Dict], breakout_day: Dict) -> float:
        """Score gap up on breakout day (0-100)"""
        if len(pre_breakout) == 0:
            return 50
        
        previous_close = float(pre_breakout[-1]['close'])
        breakout_open = float(breakout_day['open'])
        gap_percentage = ((breakout_open - previous_close) / previous_close) * 100
        
        if gap_percentage >= 5:
            return 100
        elif gap_percentage >= 2:
            return 70 + (gap_percentage - 2) * 10
        elif gap_percentage >= 0.5:
            return 50 + (gap_percentage - 0.5) * 13.33
        elif gap_percentage >= 0:
            return 30 + gap_percentage * 40
        else:
            return max(0, 30 + gap_percentage * 10)


def main():
    """Main function to run calibration analysis"""
    calibrator = BeautyModelCalibrator()
    
    print("🔬 Beauty Score Model Calibration")
    print("=" * 50)
    
    # Generate calibration report
    report = calibrator.generate_calibration_report()
    
    if 'error' in report:
        print(f"❌ Error: {report['error']}")
        return
    
    # Print summary
    summary = report['summary']
    print(f"📊 Analysis Summary:")
    print(f"   Total samples: {summary['total_samples']}")
    print(f"   Current model R²: {summary['current_model_r2']:.3f}")
    print(f"   Optimized model R²: {summary['optimized_model_r2']:.3f}")
    print()
    
    # Print grade distribution
    print("📈 Grade Distribution:")
    for grade, count in summary['grade_distribution'].items():
        percentage = (count / summary['total_samples'] * 100)
        print(f"   Grade {grade}: {count} samples ({percentage:.1f}%)")
    print()
    
    # Print current vs optimized weights
    optimization = report['optimization']
    if optimization:
        print("⚖️  Weight Comparison:")
        current_weights = optimization['current_weights']
        optimized_weights = optimization['optimized_weights']
        
        for component in current_weights:
            current = current_weights[component]
            optimized = optimized_weights.get(component, current)
            change = optimized - current
            arrow = "↗️" if change > 0 else "↘️" if change < 0 else "➡️"
            print(f"   {component}: {current:.3f} {arrow} {optimized:.3f} ({change:+.3f})")
        print()
    
    # Print recommendations
    recommendations = report['recommendations']
    if recommendations:
        print("💡 Recommendations:")
        for rec in recommendations:
            print(f"   {rec}")
        print()
    
    # Save detailed report
    output_file = 'beauty_model_calibration_report.json'
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📄 Detailed report saved to: {output_file}")


if __name__ == "__main__":
    main()