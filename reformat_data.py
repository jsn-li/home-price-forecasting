# Generated by ChatGPT
import pandas as pd

# Replace 'your_input.csv' with the path to your CSV file
input_csv_path = 'connecticut.original.csv'
output_csv_path = 'connecticut.csv'  # Replace with the desired output file path

# Read the CSV file into a pandas DataFrame
df = pd.read_csv(input_csv_path)

# Convert 'Date Recorded' column to epoch timestamps
df['Date Recorded'] = pd.to_datetime(df['Date Recorded'], errors='coerce')
df['Sale Amount'] = df['Sale Amount'].astype(int)

# Save the modified DataFrame back to CSV
df.to_csv(output_csv_path, index=False)

print(f"Conversion complete. Output saved to {output_csv_path}")
