import pandas as pd
from pathlib import Path
from typing import Optional

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

class DataLoader:
    """Class responsible for loading and initial processing of exam data."""
    
    def __init__(self, input_file: str = None, sheet_name: str = None):
        """
        Initialize the DataLoader with file path and sheet name.
        
        Args:
            input_file: Path to the Excel input file
            sheet_name: Name of the sheet to load
        """
        self.input_file = input_file or ExamRoomConfig.EXCEL_INPUT_FILE
        self.sheet_name = sheet_name or ExamRoomConfig.SHEET_NAME
        self.required_columns = ExamRoomConfig.REQUIRED_COLUMNS
        self.column_rename_mapping = ExamRoomConfig.COLUMN_RENAME_MAPPING
    
    def validate_input_file(self) -> bool:
        """
        Validate input file existence and format.
        
        Returns:
            bool: True if file is valid, False otherwise
        """
        try:
            if not Path(self.input_file).exists():
                logger.error(f"Input file {self.input_file} does not exist")
                return False
            
            df = pd.read_excel(self.input_file, sheet_name=self.sheet_name, nrows=1)
            missing_cols = set(self.required_columns) - set(df.columns)
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error validating input file: {str(e)}")
            return False
    
    def load_data(self) -> Optional[pd.DataFrame]:
        """
        Load data from Excel file and prepare initial dataframe.
        
        Returns:
            Optional[pd.DataFrame]: Processed dataframe or None if loading failed
        """
        try:
            if not self.validate_input_file():
                return None
                
            logger.info(f"Loading data from {self.input_file}")
            data = pd.read_excel(self.input_file, sheet_name=self.sheet_name)
            data = data[self.required_columns]
            data = data.rename(columns=self.column_rename_mapping)
            
            # Remove .0 from thaiID
            data["thaiID"] = data["thaiID"].astype(str).str.replace(".0", "")
            
            qualified_data = data[data["status"] == "ผ่านคุณสมบัติ"]
            
            logger.info(f"Loaded {len(qualified_data)} qualified applicants")
            return qualified_data
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return None 