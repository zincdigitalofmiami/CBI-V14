#!/usr/bin/env python3
import pandas as pd

datasets = {
    'training_final.csv': 'Basic training dataset',
    'training_ready.csv': 'Ready training dataset', 
    'training_dataset_enhanced.csv': 'Enhanced dataset v1',
    'training_dataset_final_enhanced.csv': 'Enhanced dataset v2 (FINAL)'
}

print("="*60)
print("TRAINING DATASET AUDIT SUMMARY")
print("="*60)

for filename, desc in datasets.items():
    try:
        df = pd.read_csv(filename)
        rows, cols = df.shape
        
        # Quick checks
        dupes = df.duplicated().sum()
        date_dupes = df['date'].duplicated().sum() if 'date' in df.columns else 0
        missing = df.isnull().sum().sum()
        
        # Check for 999 placeholders
        fake_999 = 0
        for col in df.select_dtypes(include=['number']).columns:
            fake_999 += (df[col] == 999).sum()
            
        # Check for excessive 0.5 values (mock sentiment)
        excessive_half = 0
        for col in df.select_dtypes(include=['float']).columns:
            count_half = (df[col] == 0.5).sum()
            if count_half > len(df) * 0.4:  # More than 40%
                excessive_half += 1
        
        print(f"\n📊 {filename}")
        print(f"   {desc}")
        print(f"   Size: {rows:,} rows × {cols} columns")
        print(f"   Issues: Dupes={dupes}, DateDupes={date_dupes}, Missing={missing}")
        print(f"   Fake: 999s={fake_999}, ExcessiveHalfs={excessive_half}")
        
        if dupes == 0 and date_dupes == 0 and missing == 0 and fake_999 == 0 and excessive_half < 5:
            print(f"   ✅ LOOKS CLEAN")
        else:
            print(f"   ⚠️  HAS ISSUES")
            
    except Exception as e:
        print(f"\n❌ {filename}: ERROR - {str(e)}")

print("\n" + "="*60)
print("RECOMMENDATION:")
print("Use 'training_dataset_final_enhanced.csv' if it's clean")
print("="*60)



