import pandas as pd
import re
from typing import Optional

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

class DataProcessor:
    """Class responsible for processing and transforming student data."""
    
    def __init__(self):
        """Initialize the DataProcessor."""
        self.school_prefixes = ExamRoomConfig.SCHOOL_PREFIXES
        self.title_mapping = ExamRoomConfig.TITLE_MAPPING
        self.exam_rooms = ExamRoomConfig.EXAM_ROOMS
        self.room_metadata = ExamRoomConfig.ROOM_METADATA
        self.exam_id_prefix = ExamRoomConfig.EXAM_ID_PREFIX
        self.final_column_rename = ExamRoomConfig.FINAL_COLUMN_RENAME
    
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
    
    def assign_exam_details(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Assign exam IDs, room numbers, and seat numbers.
        
        Args:
            df: DataFrame with student data
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with assigned exam details or None if processing failed
        """
        try:
            df = df.copy()
            df = df.sort_values(by=["firstname", "lastname"])
            
            # Initialize columns
            df["running_number"] = range(1, len(df) + 1)
            df["exam_id"] = df["program"].map(self.exam_id_prefix) + df["running_number"].astype(str).str.zfill(3)
            df["exam_room"] = ""
            df["exam_no"] = 0
            
            # Process each program separately
            for program in df["program"].unique():
                try:
                    program_mask = df["program"] == program
                    num_students = program_mask.sum()
                    
                    if program not in self.exam_rooms:
                        logger.error(f"No room configuration found for program: {program}")
                        continue
                    
                    # Get program rooms and their capacities
                    program_rooms = self.exam_rooms[program]
                    total_capacity = sum(capacity for _, capacity in program_rooms)
                    
                    if num_students > total_capacity:
                        logger.warning(f"Program {program} has more students ({num_students}) than capacity ({total_capacity})")
                    
                    # Assign room numbers and seat numbers
                    current_student = 0
                    room_assignments = []
                    exam_numbers = []
                    
                    for room_name, room_capacity in program_rooms:
                        if current_student >= num_students:
                            break
                        students_in_room = min(room_capacity, num_students - current_student)
                        room_assignments.extend([room_name] * students_in_room)
                        exam_numbers.extend(range(1, students_in_room + 1))
                        current_student += students_in_room
                        logger.debug(f"Assigned {students_in_room} students to room {room_name}")
                    
                    df.loc[program_mask, "exam_room"] = room_assignments
                    df.loc[program_mask, "exam_no"] = exam_numbers
                    # Map room to building and floor with error handling
                    for idx, room in enumerate(df.loc[program_mask, "exam_room"]):
                        if room in self.room_metadata:
                            df.loc[df.loc[program_mask].iloc[idx].name, "exam_building"] = self.room_metadata[room]["building"]
                            df.loc[df.loc[program_mask].iloc[idx].name, "exam_floor"] = self.room_metadata[room]["floor"]
                        else:
                            logger.warning(f"Room metadata not found for room: {room}")
                            df.loc[df.loc[program_mask].iloc[idx].name, "exam_building"] = "ไม่ระบุ"
                            df.loc[df.loc[program_mask].iloc[idx].name, "exam_floor"] = "ไม่ระบุ"
                    logger.info(f"Successfully assigned rooms for program {program} ({num_students} students)")
                    
                except Exception as e:
                    logger.error(f"Error processing program {program}: {str(e)}")
                    continue
            
            return df
        except Exception as e:
            logger.error(f"Error in exam detail assignment: {str(e)}")
            return None
    
    def prepare_final_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare the final dataframe for export.
        
        Args:
            df: DataFrame with assigned exam details
            
        Returns:
            pd.DataFrame: Final processed DataFrame
        """
        final_columns = ["exam_room", "exam_no", "exam_id", "fullname", "school"]
        df = df[final_columns]
        return df.rename(columns=self.final_column_rename)


    def preprocess_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Preprocess the data by cleaning and formatting.
        
        Args:
            df: DataFrame with initial student data
            
        Returns:
            Optional[pd.DataFrame]: Preprocessed DataFrame or None if preprocessing failed
        """
        try:
            df = self.clean_school_names(df)
            df = self.format_student_names(df)
            return df
        except Exception as e:
            logger.error(f"Error in data preprocessing: {str(e)}")
            return None
    
    def process_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Process the data through all processing steps.
        
        Args:
            df: DataFrame with initial student data
            
        Returns:
            Optional[pd.DataFrame]: Fully processed DataFrame or None if processing failed
        """
        try:
            # First preprocess the data
            df = self.preprocess_data(df)
            if df is None:
                return None
                
            # Then assign exam details
            df = self.assign_exam_details(df)
            if df is None:
                return None
                
            return self.prepare_final_dataframe(df)
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            return None 
        
    def process_data_firebase(self, df: pd.DataFrame) -> Optional[dict]:
        """
        Process the data through all processing steps and return a dictionary for Firebase.
        
        Args:
            df: DataFrame with initial student data

        Returns:
            Optional[dict]: Dictionary for Firebase or None if processing failed
        """
        try:
            df = self.preprocess_data(df)
            if df is None:
                return None
            
            df = self.assign_exam_details(df)
            if df is None:
                return None
            
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
            df = df[columns_to_pick]
            df = df.rename(columns=rename_mapping)

            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error in data processing for Firebase: {str(e)}")
            return None
