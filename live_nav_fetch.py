import os
import json
import requests
import pandas as pd

SCHEMES = {
    "125497": "HDFC Top 100 Direct",
    "119551": "SBI Bluechip",
    "120503": "ICICI Bluechip",
    "118632": "Nippon Large Cap",
    "119092": "Axis Bluechip",
    "120841": "Kotak Bluechip"
}

BASE_URL = "https://api.mfapi.in/mf/"
OUTPUT_DIR = "data/raw"

def fetch_and_save_nav(scheme_code, scheme_name):
    url = f"{BASE_URL}{scheme_code}"
    print(f"Fetching NAV for {scheme_name} (Code: {scheme_code})...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        json_path = os.path.join(OUTPUT_DIR, f"raw_nav_{scheme_code}.json")
        with open(json_path, "w") as f:
            json.dump(data, f, indent=4)
            
        if "data" in data and len(data["data"]) > 0:
            nav_df = pd.DataFrame(data["data"])
            nav_df["scheme_code"] = scheme_code
            nav_df["scheme_name"] = scheme_name
            
            csv_path = os.path.join(OUTPUT_DIR, f"raw_nav_{scheme_code}.csv")
            nav_df.to_csv(csv_path, index=False)
            print(f"  [✓] Saved CSV: {csv_path}")
        else:
            print(f"  [!] No NAV data found for {scheme_code}.")
            
    except requests.exceptions.RequestException as e:
        print(f"  [X] Failed fetching {scheme_code}: {e}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for code, name in SCHEMES.items():
        fetch_and_save_nav(code, name)

if __name__ == "__main__":
    main()
