# First, let's examine the sample LC and mappings to understand the structure
import pandas as pd
import json

# Load the sample LC content
with open('sampleLC.txt', 'r') as f:
    sample_lc_content = f.read()

print("Sample LC Content Preview:")
print(sample_lc_content[:1000] + "...")
print("\n" + "="*50 + "\n")

# Load the mappings data
try:
    mappings_df = pd.read_excel('mappings.xlsx', sheet_name='sonnet')
    print("Mappings DataFrame Preview:")
    print(mappings_df.head(10))
    print(f"\nTotal mappings: {len(mappings_df)}")
except Exception as e:
    print(f"Error loading mappings: {e}")