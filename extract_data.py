
import requests
import pandas as pd

# NYC 311 live public dataset API
API_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

params = {
    "$select": """
        unique_key,
        created_date,
        closed_date,
        complaint_type,
        descriptor,
        borough,
        community_board,
        incident_zip,
        latitude,
        longitude,
        status
    """,
    "$where": """
        upper(complaint_type) LIKE '%DUMP%'
        OR upper(descriptor) LIKE '%DUMP%'
    """,
    "$limit": 10000,
    "$order": "created_date DESC"
}

print("Connecting to live NYC Open Data...")
try:
    response = requests.get(API_URL, params=params, timeout=60)
    response.raise_for_status()

    data = response.json()
    df = pd.DataFrame(data)

    if df.empty:
        print("No dumping-related records returned.")
        print("We need to check alternative complaint categories.")
    else:
        # Save live records
        df.to_csv("illegal_dumping_data.csv", index=False)

        print("\nLIVE DATA EXTRACTED SUCCESSFULLY!")
        print("-" * 45)
        print("Total records:", len(df))
        print("Columns:", list(df.columns))
        print("\nComplaint categories:")
        print(df["complaint_type"].value_counts())

        print("\nBorough distribution:")
        print(df["borough"].value_counts())

        print("\nMissing values:")
        print(df.isnull().sum())

        print("\nCSV file saved:")
        print("illegal_dumping_data.csv")

except requests.exceptions.RequestException as e:
    print("API connection error:", e)

except Exception as e:
    print("Error:", e)
