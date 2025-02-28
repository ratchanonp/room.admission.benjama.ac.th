import pandas as pd
import re
from typing import Optional

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

class NameProcessor:
    """Class responsible for processing student and school names."""
    
    def __init__(self):
        """Initialize the NameProcessor."""
        self.school_prefixes = ExamRoomConfig.SCHOOL_PREFIXES
        self.title_mapping = ExamRoomConfig.TITLE_MAPPING
        # Thai leading vowels that should be skipped when sorting
        self.thai_leading_vowels = ["เ", "แ", "โ", "ใ", "ไ"]

    def clean_school_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean school names by removing prefixes and extra whitespace.
        
        Args:
            df: DataFrame with school data
            
        Returns:
            pd.DataFrame: DataFrame with cleaned school names
        """
        df = df.copy()
        pattern = r"^(" + "|".join(self.school_prefixes) + ")"
        df["school"] = df["school"].str.replace(pattern, "", regex=True)
        df["school"] = df["school"].str.strip()
        return df
    
    def format_student_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format student names with proper titles and create fullname column.
        
        Args:
            df: DataFrame with student data
            
        Returns:
            pd.DataFrame: DataFrame with formatted student names
        """
        df = df.copy()
        df["title"] = df["title"].map(self.title_mapping)
        df["firstname"] = df["firstname"].str.strip()
        df["lastname"] = df["lastname"].str.strip()
        
        df["fullname"] = (df["title"] + df["firstname"] + " " + df["lastname"])
        df["fullname"] = df["fullname"].str.strip().str.replace("  ", " ")
        return df
    
    def school_name_correction(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Correct school names based on mapping.
        
        Args:
            df: DataFrame with student data
            
        Returns:
            pd.DataFrame: DataFrame with corrected school names
        """
        df = df.copy()

        # Load the mapping file csv - disable any automatic whitespace trimming
        mapping_file = pd.read_csv(ExamRoomConfig.EXCEL_SCHOOL_NAME_MAPPING_FILE, skipinitialspace=False)
        
        # Create direct mapping with exact string matching
        # - Keep old keys exactly as they appear for exact matching
        # - Preserve new values exactly as they appear
        mapping = {}
        for item in mapping_file.to_dict(orient="records"):
            old_key = item["old"]
            new_value = item["new"]
            
            # Skip NaN keys
            if pd.isna(old_key):
                continue
            
            # Handle NaN values in the mapping
            if pd.isna(new_value):
                new_value = old_key  # Default to original if no mapping exists
            
            # Store mapping with preserved exact keys and values
            mapping[old_key] = new_value
        
        # Use mapping with a fallback to the original value if not found in mapping
        df["school"] = df["school"].apply(lambda x: mapping.get(x, x))
        
        return df
    
    def get_thai_sort_key(self, name: str) -> str:
        """
        Get a sort key for Thai names considering leading vowels.
        For names with leading vowels, returns the first consonant 
        as the primary sort character.
        
        Args:
            name: Thai name to create sort key for
            
        Returns:
            str: Sort key for the name
        """
        if not name or len(name) < 2:
            return name
            
        # If the name starts with a leading vowel, use the second character
        # as the primary sort character
        if name[0] in self.thai_leading_vowels:
            # Return the name with the first consonant first, followed by the vowel
            # This ensures proper Thai sorting
            return name[1] + name[0] + name[2:] if len(name) > 2 else name[1] + name[0]
        
        return name 