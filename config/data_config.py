import os

# Get the absolute path of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_token_cache = {"token": None, "exp": 0}
# Go one directory up (parent directory)


HOME_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))



DATA_DIR = os.path.join(HOME_DIR, "data")




IATA_CODES_FILE = os.path.join(DATA_DIR, "IATA.csv")

with open(IATA_CODES_FILE, 'r') as file:
    IATA_CODES = {}
    for line in file:
        parts = line.strip().split(',')
        if len(parts) >= 2:
            city = parts[1].strip()
            country = parts[2].strip()
            code = parts[-1].strip()
            
            IATA_CODES[city] = {'code':code, 'country':country}


