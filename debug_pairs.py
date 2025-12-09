
import os

files = [
    "EURUSD1.csv", "EURUSD1440.csv", "EURUSD15.csv", "EURUSD240.csv", 
    "EURUSD30.csv", "EURUSD5.csv", "EURUSD60.csv",
    "GBPJPY1.csv", "GBPJPY1440.csv", "GBPJPY15.csv", "GBPJPY240.csv",
    "GBPJPY30.csv", "GBPJPY5.csv", "GBPJPY60.csv",
    "GBPUSD1.csv", "GBPUSD1440.csv", "GBPUSD15.csv", "GBPUSD240.csv",
    "GBPUSD30.csv", "GBPUSD5.csv", "GBPUSD60.csv",
    "USDCAD1.csv", "USDCAD1440.csv", "USDCAD15.csv", "USDCAD240.csv",
    "USDCAD30.csv", "USDCAD5.csv", "USDCAD60.csv"
]

known_tfs = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "1", "5", "15", "30", "60", "240", "1440"]

pairs = set()

for file in files:
    name = file.replace(".csv", "")
    bg = name.upper()
    
    parsed_pair = bg
    # Logic from data.py
    for tf in sorted(known_tfs, key=len, reverse=True):
        if bg.endswith(tf):
            parsed_pair = bg[:-len(tf)]
            break
            
    print(f"{file} -> {parsed_pair}")
    pairs.add(parsed_pair)

print("\nFinal Pairs:")
for p in sorted(list(pairs)):
    print(p)
