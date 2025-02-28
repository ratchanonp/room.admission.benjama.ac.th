import pandas as pd
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from exam_room_app.data_processing.data_processor import DataProcessor

def main():
    """
    Demonstrate Thai name sorting with a realistic sample.
    """
    # Create a realistic sample of Thai names
    data = {
        "firstname": [
            "อภิชาติ", "เกรียงศักดิ์", "สมชาย", "แสงดาว", "โอภาส", 
            "กมลชนก", "เมธาวี", "ไตรภพ", "นภาพร", "สุทธิดา"
        ],
        "lastname": [
            "รักเรียน", "มานะดี", "ใจสะอาด", "สว่างเนตร", "มณีรัตน์",
            "เพชรรัตน์", "วิไลพร", "แสนสุข", "ทองดี", "เรืองโรจน์"
        ],
        "thaiID": [
            "1111111111111", "2222222222222", "3333333333333", "4444444444444", "5555555555555",
            "6666666666666", "7777777777777", "8888888888888", "9999999999999", "1010101010101"
        ],
        "program": ["test-program"] * 10,
        "title": ["นาย", "นาย", "นาย", "นางสาว", "นาย", 
                 "นางสาว", "นางสาว", "นาย", "นางสาว", "นางสาว"],
        "school": ["School A"] * 10
    }
    
    df = pd.DataFrame(data)
    
    # Create processor instance
    processor = DataProcessor()
    
    # Print original data
    print("\nOriginal data:")
    print(df[["firstname", "lastname"]].to_string(index=False))
    
    # Apply sorting key
    df["firstname_sort_key"] = df["firstname"].apply(processor._get_thai_sort_key)
    df["lastname_sort_key"] = df["lastname"].apply(processor._get_thai_sort_key)
    
    # Print sort keys
    print("\nSort keys:")
    for i, row in df.iterrows():
        print(f"{row['firstname']} -> {row['firstname_sort_key']}")
    
    # Sort data
    sorted_df = df.sort_values(by=["firstname_sort_key", "lastname_sort_key"])
    
    # Print sorted data
    print("\nSorted data (correct Thai sorting):")
    print(sorted_df[["firstname", "lastname"]].to_string(index=False))
    
    # Compare with regular sorting (incorrect for Thai)
    regular_sorted = df.sort_values(by=["firstname", "lastname"])
    
    # Print regular sorted data
    print("\nRegular sorted data (incorrect for Thai):")
    print(regular_sorted[["firstname", "lastname"]].to_string(index=False))
    
    # The difference is clear: names with leading vowels are correctly 
    # sorted by their first consonant in our implementation, but would be 
    # grouped together incorrectly in regular sorting

if __name__ == "__main__":
    main() 