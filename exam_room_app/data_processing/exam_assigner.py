import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple, Set

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger
from exam_room_app.data_processing.name_processor import NameProcessor

class ExamAssigner:
    """Class responsible for assigning exam rooms, seats, and IDs to students."""
    
    def __init__(self):
        """Initialize the ExamAssigner."""
        self.exam_rooms = ExamRoomConfig.EXAM_ROOMS
        self.room_metadata = ExamRoomConfig.ROOM_METADATA
        self.exam_id_prefix = ExamRoomConfig.EXAM_ID_PREFIX
        self.name_processor = NameProcessor()

    def _get_highest_exam_id_by_program(self, checkpoint_data: Dict) -> Dict[str, int]:
        """
        Find highest exam ID for each program in checkpoint data.
        
        Args:
            checkpoint_data: Dictionary with checkpoint data
            
        Returns:
            Dict[str, int]: Dictionary with highest exam ID for each program
        """
        program_highest_exam_id = {}
        
        for key, details in checkpoint_data.items():
            program = key[1]  # Program is the second part of the key tuple
            exam_id = str(details['exam_id'])  # Ensure exam_id is a string
            
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
        
        return program_highest_exam_id
    
    def _get_room_occupancy(self, checkpoint_data: Dict, program: str) -> Dict[str, List[int]]:
        """
        Get current room occupancy from checkpoint data.
        
        Args:
            checkpoint_data: Dictionary with checkpoint data
            program: Program to check occupancy for
            
        Returns:
            Dict[str, List[int]]: Dictionary with room occupancy
        """
        room_occupancy = {}
        
        # Examine checkpoint data to find current highest exam_no for each room
        for key, details in checkpoint_data.items():
            if key[1] == program and details['exam_room']:  # Match program and has a room
                room = details['exam_room']
                if room not in room_occupancy:
                    room_occupancy[room] = []
                room_occupancy[room].append(details['exam_no'])
        
        return room_occupancy
    
    def assign_exam_details(self, df: pd.DataFrame, checkpoint_data: Dict = None) -> pd.DataFrame:
        """
        Assign exam IDs, room numbers, and seat numbers.
        
        Args:
            df: DataFrame with student data
            checkpoint_data: Dictionary with checkpoint data
            
        Returns:
            pd.DataFrame: DataFrame with assigned exam details
        """
        if checkpoint_data is None:
            checkpoint_data = {}
            
        df = df.copy()
        
        # Track which students already have exam IDs in checkpoint data
        students_with_exam_ids = set()
        
        # Find highest exam ID for each program in checkpoint data
        program_highest_exam_id = self._get_highest_exam_id_by_program(checkpoint_data)
        logger.debug(f"Highest exam ID numbers from checkpoint: {program_highest_exam_id}")
        
        # Sort by firstname and lastname, considering Thai leading vowels
        df["firstname_sort_key"] = df["firstname"].apply(self.name_processor.get_thai_sort_key)
        df["lastname_sort_key"] = df["lastname"].apply(self.name_processor.get_thai_sort_key)
        df = df.sort_values(by=["firstname_sort_key", "lastname_sort_key"])
        # Drop the temporary columns
        df = df.drop(columns=["firstname_sort_key", "lastname_sort_key"])
        
        # Add students with exam IDs to the set
        for key, details in checkpoint_data.items():
            # Add this student to the set of students with exam IDs
            students_with_exam_ids.add(key)
        
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
        
        # Process each program separately for room assignment
        self._assign_rooms_by_program(df, checkpoint_data)
        
        # Ensure exam_no is an integer to remove decimal points
        df["exam_no"] = df["exam_no"].astype(int)
        
        return df
    
    def _assign_rooms_by_program(self, df: pd.DataFrame, checkpoint_data: Dict) -> None:
        """
        Assign rooms for each program.
        
        Args:
            df: DataFrame with student data
            checkpoint_data: Dictionary with checkpoint data
        """
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
                
                # Get room occupancy from checkpoint data
                room_occupancy = self._get_room_occupancy(checkpoint_data, program)
                
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
                
                logger.info(f"Successfully assigned rooms for {num_students} unassigned students in program {program}")
                
            except Exception as e:
                logger.error(f"Error processing program {program}: {str(e)}")
                continue 