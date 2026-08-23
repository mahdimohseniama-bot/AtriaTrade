"""
Data Manager for AtriaTrade.
Handles saving and loading historical market data.
"""

import os
import csv
import json
from typing import List, Dict, Any, Optional

class DataManager:
    def __init__(self, base_path: str = "data/historical"):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def save_to_csv(self, symbol: str, data: List[Dict[str, Any]], filename: Optional[str] = None):
        """Saves OHLCV data to a CSV file."""
        if not data:
            return
        
        if filename is None:
            filename = f"{symbol.upper()}_data.csv"
            
        file_path = os.path.join(self.base_path, filename)
        keys = data[0].keys()
        
        with open(file_path, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
        return file_path

    def load_from_csv(self, symbol: str, filename: Optional[str] = None) -> List[Dict[str, Any]]:
        """Loads OHLCV data from a CSV file."""
        if filename is None:
            filename = f"{symbol.upper()}_data.csv"
            
        file_path = os.path.join(self.base_path, filename)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No data file found for {symbol}")
            
        data = []
        with open(file_path, 'r') as input_file:
            reader = csv.DictReader(input_file)
            for row in reader:
                # Convert numeric strings back to float/int
                processed_row = {}
                for k, v in row.items():
                    try:
                        if k == 'timestamp':
                            processed_row[k] = int(v)
                        else:
                            processed_row[k] = float(v) if '.' in v or v.isdigit() else v
                    except ValueError:
                        processed_row[k] = v
                data.append(processed_row)
        return data

    def get_status(self) -> Dict[str, Any]:
        files = os.listdir(self.base_path)
        return {
            "storage_path": self.base_path,
            "available_files": files,
            "file_count": len(files)
        }
