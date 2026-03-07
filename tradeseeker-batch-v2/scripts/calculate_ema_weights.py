#!/usr/bin/env python3
"""
Calculate and display EMA model weights for all 21 days
"""

def calculate_ema_weights(num_days=21):
    """
    Calculate the exact weights used in EMA model for time-based weighting
    
    Formula: weight = 1.0 - (position_from_end * 0.7 / max(1, len(recent_data) - 1))
    where position_from_end = 0 for most recent day
    """
    weights = []
    
    for i in range(num_days):
        # position_from_end calculation (0 = most recent, matches EMA model)
        position_from_end = i  # i=0 is most recent (today)
        
        # Weight calculation using EMA model formula
        weight = 1.0 - (position_from_end * 0.7 / max(1, num_days - 1))
        
        weights.append({
            'day': i + 1,
            'position_from_end': position_from_end,
            'weight': weight,
            'percentage': weight * 100
        })
    
    return weights

def display_weights():
    """Display the complete 21-day weight distribution"""
    print("🔢 EMA Model: 21-Day Weight Distribution")
    print("=" * 60)
    print(f"{'Day':<6} {'Position':<10} {'Weight':<10} {'Percentage':<12} {'Impact'}")
    print("-" * 60)
    
    weights = calculate_ema_weights(21)
    total_weight = sum(w['weight'] for w in weights)
    
    for w in weights:
        day_label = f"Day {w['day']}"
        if w['day'] == 1:
            day_label += " (Today)"
        elif w['day'] == 21:
            day_label += " (Oldest)"
            
        impact = "High" if w['percentage'] >= 79 else "Medium" if w['percentage'] >= 54.5 else "Low"
        
        print(f"{day_label:<6} {w['position_from_end']:<10} {w['weight']:<10.3f} {w['percentage']:<12.1f}% {impact}")
    
    print("-" * 60)
    print(f"Total Weight Sum: {total_weight:.2f}")
    print(f"Weight Decay per Day: {(weights[0]['weight'] - weights[-1]['weight']) / 20:.3f} ({((weights[0]['weight'] - weights[-1]['weight']) / 20) * 100:.1f}%)")
    
    # Show weight groups
    print("\n📊 Weight Groups:")
    high_impact = [w for w in weights if w['percentage'] >= 79]
    medium_impact = [w for w in weights if 54.5 <= w['percentage'] < 79]
    low_impact = [w for w in weights if w['percentage'] < 54.5]
    
    print(f"  High Impact (Days 1-{len(high_impact)}):   {high_impact[0]['percentage']:.1f}% - {high_impact[-1]['percentage']:.1f}% weight")
    print(f"  Medium Impact (Days {len(high_impact)+1}-{len(high_impact)+len(medium_impact)}): {medium_impact[0]['percentage']:.1f}% - {medium_impact[-1]['percentage']:.1f}% weight")
    print(f"  Low Impact (Days {len(high_impact)+len(medium_impact)+1}-21):    {low_impact[0]['percentage']:.1f}% - {low_impact[-1]['percentage']:.1f}% weight")

def example_calculation():
    """Show example calculation with sample data"""
    print("\n💡 Example Calculation:")
    print("=" * 60)
    print("Scenario: Stock with perfect recent performance, declining historically")
    print()
    
    weights = calculate_ema_weights(21)
    
    # Sample scores (4/4 EMAs for first 3 days, 3/4 for next 2, etc.)
    sample_scores = [100, 100, 100, 75, 75, 50, 50, 50, 25, 25, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    
    print(f"{'Day':<6} {'Score':<8} {'Weight':<8} {'Weighted':<10}")
    print("-" * 35)
    
    weighted_sum = 0
    total_weight = 0
    
    for i, (w, score) in enumerate(zip(weights[:10], sample_scores[:10])):  # Show first 10 days
        weighted_score = score * w['weight']
        weighted_sum += weighted_score
        total_weight += w['weight']
        
        print(f"Day {w['day']:<2} {score:<8} {w['weight']:<8.3f} {weighted_score:<10.1f}")
    
    print("...")
    
    # Add remaining days
    for w, score in zip(weights[10:], sample_scores[10:]):
        weighted_score = score * w['weight']
        weighted_sum += weighted_score
        total_weight += w['weight']
    
    final_score = weighted_sum / total_weight
    print(f"\nFinal Score = {weighted_sum:.1f} / {total_weight:.2f} = {final_score:.1f}")

if __name__ == "__main__":
    display_weights()
    example_calculation()