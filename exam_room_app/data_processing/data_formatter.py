import pandas as pd
from typing import Dict, List, Optional

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

class DataFormatter:
    """Class responsible for formatting data for different output formats."""
    
    def __init__(self):
        """Initialize the DataFormatter."""
        self.final_column_rename = ExamRoomConfig.FINAL_COLUMN_RENAME
    
    def prepare_final_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare the final dataframe for export.
        
        Args:
            df: DataFrame with assigned exam details
            
        Returns:
            pd.DataFrame: Final processed DataFrame sorted by exam_id
        """
        # Ensure exam_no is an integer to remove decimal points
        df["exam_no"] = df["exam_no"].astype(int)
        
        final_columns = ["exam_room", "exam_no", "exam_id", "fullname", "school"]
        df = df[final_columns]
        
        # Sort the DataFrame by exam_id
        df = df.sort_values(by="exam_id")
        
        return df.rename(columns=self.final_column_rename)
    
    def format_for_firebase(self, df: pd.DataFrame) -> List[Dict]:
        """
        Format data for Firebase.
        
        Args:
            df: DataFrame with student data
            
        Returns:
            List[Dict]: List of dictionaries for Firebase
        """
        # Ensure exam_no is an integer to remove decimal points
        df["exam_no"] = df["exam_no"].astype(int)
        
        # Pick some columns
        columns_to_pick = ["exam_id", "thaiID", "program", "exam_room", "exam_no", "exam_building", "exam_floor"]
        rename_mapping = {
            "exam_id": "examID",
            "thaiID": "thaiID",
            "program": "programID",
            "exam_room": "examRoom",
            "exam_no": "examNo",
            "exam_building": "examBuilding",
            "exam_floor": "examFloor"
        }
        
        df = df[columns_to_pick].copy()
        df = df.rename(columns=rename_mapping)
        
        return df.to_dict(orient="records")
    
    def format_school_data_for_firebase(self, df: pd.DataFrame) -> List[Dict]:
        """
        Format school data for Firebase.
        
        Args:
            df: DataFrame with student data
            
        Returns:
            List[Dict]: List of dictionaries for Firebase
        """
        df = df[["thaiID", "school"]].copy()
        df = df.rename(columns={"school": "newSchool"})
        return df.to_dict(orient="records") 