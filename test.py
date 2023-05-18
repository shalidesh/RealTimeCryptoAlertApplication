import pandas as pd
# Create a sample DataFrame
import chardet
import json


with open('./data/assetsummaries.csv', 'rb') as f:
    result = chardet.detect(f.read())
    df = pd.read_csv('./data/assetsummaries.csv', encoding=result['encoding'])


# Group the DataFrame by column 'B'
grouped = df.groupby('Ticker')

# Extract the group for 'B' == 'x'
group = grouped.get_group('BNB')

# Convert the records in the group to JSON format
json_data = group.to_json(orient='records')

# Load the JSON data as a list of dictionaries
data = json.loads(json_data)

for item in data:
    name = item['Ticker']
    age = item['Summary']
    print(name)
    print(age)

