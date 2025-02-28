import pandas as pd
import re
from typing import Optional
import os
import shutil
import numpy as np

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
    
    def _get_thai_sort_key(self, name: str) -> str:
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
    
    def assign_exam_details(self, df: pd.DataFrame, checkpoint_file: str = None) -> Optional[pd.DataFrame]:
        """
        Assign exam IDs, room numbers, and seat numbers.
        
        Args:
            df: DataFrame with student data
            checkpoint_file: Optional path to a CSV file to store/load checkpoint data
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with assigned exam details or None if processing failed
        """
        try:
            df = df.copy()
            
            # Load checkpoint data if file exists
            checkpoint_data = {}
            if checkpoint_file and os.path.exists(checkpoint_file):
                try:
                    checkpoint_df = pd.read_csv(checkpoint_file)
                    
                    # Verify required columns exist in the checkpoint file
                    required_columns = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_no']
                    missing_columns = [col for col in required_columns if col not in checkpoint_df.columns]
                    
                    if missing_columns:
                        logger.warning(f"Checkpoint file is missing required columns: {missing_columns}. Continuing with empty checkpoint data.")
                        checkpoint_data = {}
                    else:
                        # Create a dictionary with (thaiID, program) as key and exam details as value
                        for _, row in checkpoint_df.iterrows():
                            # Ensure key components are strings to avoid type issues
                            key = (str(row['thaiID']), str(row['program']))
                            checkpoint_data[key] = {
                                'exam_id': str(row['exam_id']),  # Ensure exam_id is a string
                                'exam_room': str(row['exam_room']),
                                'exam_no': int(row['exam_no']),  # Convert to integer to remove decimal points
                                'exam_building': str(row.get('exam_building', 'ไม่ระบุ')),
                                'exam_floor': str(row.get('exam_floor', 'ไม่ระบุ'))
                            }
                        logger.info(f"Loaded {len(checkpoint_data)} checkpoint records from {checkpoint_file}")
                except Exception as e:
                    logger.error(f"Error loading checkpoint data: {str(e)}")
                    
                    # Try loading from backup if available
                    checkpoint_backup = f"{checkpoint_file}.bak"
                    if os.path.exists(checkpoint_backup):
                        try:
                            logger.info(f"Attempting to load checkpoint data from backup: {checkpoint_backup}")
                            backup_df = pd.read_csv(checkpoint_backup)
                            checkpoint_data = {}
                            
                            # Verify backup data has required columns
                            required_columns = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_no']
                            if all(col in backup_df.columns for col in required_columns):
                                for _, row in backup_df.iterrows():
                                    key = (str(row['thaiID']), str(row['program']))
                                    checkpoint_data[key] = {
                                        'exam_id': str(row['exam_id']),  # Ensure exam_id is a string
                                        'exam_room': str(row['exam_room']),
                                        'exam_no': int(row['exam_no']),  # Convert to integer to remove decimal points
                                        'exam_building': str(row.get('exam_building', 'ไม่ระบุ')),
                                        'exam_floor': str(row.get('exam_floor', 'ไม่ระบุ'))
                                    }
                                logger.info(f"Successfully loaded {len(checkpoint_data)} checkpoint records from backup")
                            else:
                                logger.warning("Backup checkpoint file is missing required columns. Continuing with empty checkpoint data.")
                        except Exception as backup_error:
                            logger.error(f"Error loading checkpoint data from backup: {str(backup_error)}")
                            # Continue with empty checkpoint data
                            checkpoint_data = {}
                    else:
                        # Continue with empty checkpoint data
                        checkpoint_data = {}
            
            # Sort by firstname and lastname, considering Thai leading vowels
            df["firstname_sort_key"] = df["firstname"].apply(self._get_thai_sort_key)
            df["lastname_sort_key"] = df["lastname"].apply(self._get_thai_sort_key)
            df = df.sort_values(by=["firstname_sort_key", "lastname_sort_key"])
            # Drop the temporary columns
            df = df.drop(columns=["firstname_sort_key", "lastname_sort_key"])
            
            # Find highest exam ID for each program in checkpoint data
            program_highest_exam_id = {}
            # Track which students already have exam IDs in checkpoint data
            students_with_exam_ids = set()
            if checkpoint_data:
                for key, details in checkpoint_data.items():
                    program = key[1]  # Program is the second part of the key tuple
                    exam_id = str(details['exam_id'])  # Ensure exam_id is a string
                    
                    # Add this student to the set of students with exam IDs
                    students_with_exam_ids.add(key)
                    
                    # Extract the numeric part of the exam ID by removing the prefix
                    if program in self.exam_id_prefix:
                        prefix = self.exam_id_prefix[program]
                        logger.debug(f"Exam ID prefix for program {program}: {prefix}")
                        if exam_id.startswith(prefix):
                            try:
                                id_number = int(exam_id[len(prefix):])
                                logger.debug(f"Exam ID number for program {program}: {exam_id}")
                                program_highest_exam_id[program] = max(program_highest_exam_id.get(program, 0), id_number)
                                logger.debug(f"Highest exam ID number for program {program}: {program_highest_exam_id[program]}")
                            except (ValueError, TypeError):
                                # If parsing fails, just continue
                                logger.warning(f"Could not parse exam ID number from '{exam_id}' for program '{program}'")
            
            logger.debug(f"Highest exam ID numbers from checkpoint: {program_highest_exam_id}")
            
            # Initialize columns with updated running numbers
            df["running_number"] = 0  # Initialize with 0, will be updated per program
            
            # Update running numbers program by program to continue from checkpoint data
            for program in df["program"].unique():
                # Get the highest exam ID number for this program, default to 0 if none exists
                highest_id = program_highest_exam_id.get(program, 0)
                
                # Get initial count of students in this program
                program_mask = df["program"] == program
                total_students = program_mask.sum()
                
                # Create a mask for new students (initially all students in the program)
                new_students_mask = program_mask.copy()
                
                # Count of students who already have exam IDs
                skipped_students = 0
                
                if checkpoint_data:
                    # Filter out students who already have exam IDs
                    for idx in df[program_mask].index:
                        key = (str(df.loc[idx, 'thaiID']), str(df.loc[idx, 'program']))
                        if key in students_with_exam_ids:
                            new_students_mask.loc[idx] = False
                            skipped_students += 1
                
                # Count new students who need exam IDs
                num_new_students = new_students_mask.sum()
                
                logger.debug(f"Program {program}: {skipped_students} students have existing exam IDs, {num_new_students} need new exam IDs")
                
                if num_new_students > 0:
                    # Set running numbers only for new students, starting after the highest existing ID
                    running_numbers = list(range(highest_id + 1, highest_id + num_new_students + 1))
                    df.loc[new_students_mask, "running_number"] = running_numbers
                    logger.debug(f"Assigned running numbers {highest_id + 1} to {highest_id + num_new_students} for {num_new_students} new students in program {program}")
            
            # Generate exam IDs based on running numbers only for students with non-zero running numbers
            # (those who don't already have exam IDs in checkpoint data)
            new_students_mask = df["running_number"] > 0
            if new_students_mask.any():
                df.loc[new_students_mask, "exam_id"] = df.loc[new_students_mask].apply(
                    lambda row: self.exam_id_prefix.get(row["program"], "") + str(row["running_number"]).zfill(3), 
                    axis=1
                )
            
            # Initialize other columns for new students
            df.loc[new_students_mask, "exam_room"] = ""
            df.loc[new_students_mask, "exam_no"] = 0
            df.loc[new_students_mask, "exam_building"] = "ไม่ระบุ"
            df.loc[new_students_mask, "exam_floor"] = "ไม่ระบุ"
            
            # Apply checkpoint data first
            skipped_count = 0
            skipped_by_program = {}
            if checkpoint_data:
                for idx, row in df.iterrows():
                    # Ensure key components are strings to avoid type issues
                    key = (str(row['thaiID']), str(row['program']))
                    if key in checkpoint_data:
                        # Apply saved exam details from checkpoint
                        for field, value in checkpoint_data[key].items():
                            df.at[idx, field] = value
                        logger.debug(f"Applied checkpoint data for student {row['thaiID']} in program {row['program']}")
                        
                        # Track skipped students for logging
                        skipped_count += 1
                        program = row['program']
                        if program in skipped_by_program:
                            skipped_by_program[program] += 1
                        else:
                            skipped_by_program[program] = 1
                
                # Log summary of skipped students
                if skipped_count > 0:
                    logger.info(f"Skipped room assignment for {skipped_count} students using existing checkpoint data")
                    for program, count in skipped_by_program.items():
                        logger.info(f"  - Program {program}: {count} students using existing room assignments")
            
            # Process each program separately
            for program in df["program"].unique():
                try:
                    # Filter students who don't have room assignments yet
                    program_mask = (df["program"] == program) & (df["exam_room"] == "")
                    num_students = program_mask.sum()
                    
                    if num_students == 0:
                        logger.info(f"All students in program {program} already have room assignments from checkpoint")
                        continue
                    
                    if program not in self.exam_rooms:
                        logger.error(f"No room configuration found for program: {program}")
                        continue
                    
                    # Get program rooms and their capacities
                    program_rooms = self.exam_rooms[program]
                    total_capacity = sum(capacity for _, capacity in program_rooms)
                    
                    if num_students > total_capacity:
                        logger.warning(f"Program {program} has more students ({num_students}) than capacity ({total_capacity})")
                    
                    # Get room occupancy from checkpoint data to continue numbering
                    room_occupancy = {}
                    if checkpoint_data:
                        # Examine checkpoint data to find current highest exam_no for each room
                        for key, details in checkpoint_data.items():
                            if key[1] == program and details['exam_room']:  # Match program and has a room
                                room = details['exam_room']
                                if room not in room_occupancy:
                                    room_occupancy[room] = []
                                room_occupancy[room].append(details['exam_no'])
                    
                    # Find the highest exam number for each room
                    room_highest_exam_no = {}
                    for room, numbers in room_occupancy.items():
                        room_highest_exam_no[room] = max(numbers) if numbers else 0
                    
                    logger.debug(f"Current room occupancy for program {program}: {room_highest_exam_no}")
                    
                    # Assign room numbers and seat numbers
                    current_student = 0
                    room_assignments = []
                    exam_numbers = []
                    
                    for room_name, room_capacity in program_rooms:
                        if current_student >= num_students:
                            break
                        
                        # Calculate remaining capacity based on highest existing exam number
                        highest_exam_no = room_highest_exam_no.get(room_name, 0)
                        remaining_capacity = room_capacity - highest_exam_no
                        
                        if remaining_capacity <= 0:
                            logger.warning(f"Room {room_name} is already at capacity from checkpoint data, skipping")
                            continue
                            
                        students_in_room = min(remaining_capacity, num_students - current_student)
                        room_assignments.extend([room_name] * students_in_room)
                        
                        # Continue numbering from the highest existing exam number
                        start_number = highest_exam_no + 1
                        exam_numbers.extend(range(start_number, start_number + students_in_room))
                        
                        current_student += students_in_room
                        logger.debug(f"Assigned {students_in_room} students to room {room_name} (seats {start_number}-{start_number+students_in_room-1})")
                    
                    # Get indices of students without room assignments
                    unassigned_indices = df.index[program_mask].tolist()
                    
                    # Assign rooms and numbers to unassigned students
                    df.loc[unassigned_indices, "exam_room"] = room_assignments
                    df.loc[unassigned_indices, "exam_no"] = exam_numbers
                    
                    # Map room to building and floor with error handling
                    for idx in unassigned_indices:
                        room = df.loc[idx, "exam_room"]
                        if room in self.room_metadata:
                            df.loc[idx, "exam_building"] = self.room_metadata[room]["building"]
                            df.loc[idx, "exam_floor"] = self.room_metadata[room]["floor"]
                        else:
                            logger.warning(f"Room metadata not found for room: {room}")
                            df.loc[idx, "exam_building"] = "ไม่ระบุ"
                            df.loc[idx, "exam_floor"] = "ไม่ระบุ"
                    
                    # Ensure exam_no is an integer to remove decimal points
                    df["exam_no"] = df["exam_no"].astype(int)
                    
                    logger.info(f"Successfully assigned rooms for {num_students} unassigned students in program {program}")
                    
                except Exception as e:
                    logger.error(f"Error processing program {program}: {str(e)}")
                    continue
            
            # Save checkpoint data if file is specified
            if checkpoint_file:
                try:
                    checkpoint_columns = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_no', 'exam_building', 'exam_floor']
                    
                    # Ensure all required columns exist in the dataframe
                    missing_columns = [col for col in checkpoint_columns if col not in df.columns]
                    if missing_columns:
                        logger.error(f"Cannot save checkpoint: Missing columns in data: {missing_columns}")
                        raise ValueError(f"Missing required columns for checkpoint: {missing_columns}")
                    
                    # Extract only the needed columns
                    current_program_data = df[checkpoint_columns].copy()
                    
                    # Check if checkpoint file already exists
                    if os.path.exists(checkpoint_file):
                        # Load existing checkpoint data
                        existing_checkpoint = pd.read_csv(checkpoint_file)
                        
                        # Create explicit copies to avoid SettingWithCopyWarning
                        existing_checkpoint = existing_checkpoint.copy()
                        current_program_data = current_program_data.copy()
                        
                        # Ensure consistent data types for columns - using modern pandas approach to avoid FutureWarning
                        # Handle all text columns that should be strings
                        string_columns = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_building', 'exam_floor']
                        
                        # Convert all string columns properly to avoid incompatible dtype warnings
                        for col in string_columns:
                            if col in existing_checkpoint.columns:
                                # Convert to strings first, then handle nulls separately to avoid FutureWarning
                                existing_checkpoint[col] = existing_checkpoint[col].astype(str)
                                existing_checkpoint.loc[existing_checkpoint[col] == 'nan', col] = ''
                            
                            if col in current_program_data.columns:
                                # Convert to strings first, then handle nulls separately to avoid FutureWarning
                                current_program_data[col] = current_program_data[col].astype(str)
                                current_program_data.loc[current_program_data[col] == 'nan', col] = ''
                        
                        # Handle numeric fields - create new Series with int dtype
                        if 'exam_no' in existing_checkpoint.columns:
                            # Handle numeric conversion without warnings
                            existing_checkpoint['exam_no'] = existing_checkpoint['exam_no'].replace([None, np.nan], 0)
                            existing_checkpoint['exam_no'] = existing_checkpoint['exam_no'].astype(int)
                        
                        if 'exam_no' in current_program_data.columns:
                            # Handle numeric conversion without warnings
                            current_program_data['exam_no'] = current_program_data['exam_no'].replace([None, np.nan], 0)
                            current_program_data['exam_no'] = current_program_data['exam_no'].astype(int)
                        
                        # Create a composite key for merging - ensure values are strings to avoid type errors
                        existing_checkpoint['key'] = existing_checkpoint['thaiID'].astype(str) + '_' + existing_checkpoint['program'].astype(str)
                        current_program_data['key'] = current_program_data['thaiID'].astype(str) + '_' + current_program_data['program'].astype(str)
                        
                        # Remove rows from existing data that are being updated
                        existing_keys = set(current_program_data['key'])
                        existing_checkpoint = existing_checkpoint[~existing_checkpoint['key'].isin(existing_keys)]
                        
                        # Drop the temporary key column - make explicit copies to avoid SettingWithCopyWarning
                        existing_checkpoint = existing_checkpoint.drop(columns=['key'])
                        current_program_data = current_program_data.drop(columns=['key'])
                        
                        # Combine the remaining existing data with updated data
                        combined_data = pd.concat([existing_checkpoint, current_program_data], ignore_index=True)
                        
                        # Save the combined data with backup before overwriting
                        checkpoint_backup = f"{checkpoint_file}.bak"
                        if os.path.exists(checkpoint_file):
                            try:
                                # Create a backup of the existing file before overwriting
                                shutil.copy2(checkpoint_file, checkpoint_backup)
                                logger.debug(f"Created backup of checkpoint file: {checkpoint_backup}")
                            except Exception as backup_error:
                                logger.warning(f"Failed to create backup of checkpoint file: {str(backup_error)}")
                        
                        # Save the combined data
                        combined_data.to_csv(checkpoint_file, index=False)
                        logger.info(f"Updated checkpoint file with {len(current_program_data)} records, total records: {len(combined_data)}")
                    else:
                        # No existing file, just save current data - ensure it's a copy
                        current_program_data = current_program_data.copy()
                        current_program_data.to_csv(checkpoint_file, index=False)
                        logger.info(f"Created new checkpoint file with {len(current_program_data)} records")
                        
                except Exception as e:
                    logger.error(f"Error saving checkpoint data: {str(e)}")
                    # Add more diagnostic information
                    try:
                        # Log data types to help diagnose issues
                        if 'current_program_data' in locals():
                            logger.debug(f"Current program data types: {current_program_data.dtypes}")
                        if 'existing_checkpoint' in locals():
                            logger.debug(f"Existing checkpoint data types: {existing_checkpoint.dtypes}")
                        logger.error(f"Checkpoint save error details: {type(e).__name__} - {str(e)}")
                    except Exception as debug_error:
                        logger.error(f"Error while trying to log debug info: {str(debug_error)}")
            
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
            pd.DataFrame: Final processed DataFrame sorted by exam_id
        """
        # Ensure exam_no is an integer to remove decimal points
        df["exam_no"] = df["exam_no"].astype(int)
        
        final_columns = ["exam_room", "exam_no", "exam_id", "fullname", "school"]
        df = df[final_columns]
        
        # Sort the DataFrame by exam_id
        df = df.sort_values(by="exam_id")
        
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
            df = self.school_name_correction(df)
            return df
        except Exception as e:
            logger.error(f"Error in data preprocessing: {str(e)}")
            return None
    
    def process_data(self, df: pd.DataFrame, checkpoint_file: str = None) -> Optional[pd.DataFrame]:
        """
        Process the data through all processing steps.
        
        Args:
            df: DataFrame with initial student data
            checkpoint_file: Optional path to a CSV file to store/load checkpoint data
            
        Returns:
            Optional[pd.DataFrame]: Fully processed DataFrame or None if processing failed
        """
        try:
            # First preprocess the data
            df = self.preprocess_data(df)
            if df is None:
                return None
                
            # Then assign exam details
            df = self.assign_exam_details(df, checkpoint_file)
            if df is None:
                return None
            
                
            return self.prepare_final_dataframe(df)
        except Exception as e:
            logger.error(f"Error in data processing: {str(e)}")
            return None
    
    def process_data_firebase(self, df: pd.DataFrame, checkpoint_file: str = None) -> Optional[dict]:
        """
        Process the data through all processing steps and return a dictionary for Firebase.
        
        Args:
            df: DataFrame with initial student data
            checkpoint_file: Optional path to a CSV file to store/load checkpoint data

        Returns:
            Optional[dict]: Dictionary for Firebase or None if processing failed
        """
        try:
            df = self.preprocess_data(df)
            if df is None:
                return None
            
            df = self.assign_exam_details(df, checkpoint_file)
            if df is None:
                return None
            
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
            df = df[columns_to_pick]
            df = df.rename(columns=rename_mapping)

            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error in data processing for Firebase: {str(e)}")
            return None

    def process_new_school_data_firebase(self, df: pd.DataFrame) -> Optional[dict]:
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

            df = df[["thaiID", "school"]]
            df = df.rename(columns={"school": "newSchool"})
            return df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error in data processing for Firebase: {str(e)}")
            return None
            