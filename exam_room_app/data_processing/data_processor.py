import pandas as pd
import traceback
from typing import Optional, Dict, List, Tuple, Any, Callable, Union, Set

from exam_room_app.utils.logger import logger
from exam_room_app.data_processing.name_processor import NameProcessor
from exam_room_app.data_processing.exam_assigner import ExamAssigner
from exam_room_app.data_processing.checkpoint_manager import CheckpointManager
from exam_room_app.data_processing.data_formatter import DataFormatter

class DataProcessor:
    """
    Main class responsible for orchestrating the entire data processing workflow.
    
    This class delegates specific tasks to specialized processing classes
    and provides a unified interface for data processing operations.
    
    Attributes:
        name_processor: Handles processing and cleaning of names
        exam_assigner: Assigns exam room details to students
        checkpoint_manager: Handles saving and loading checkpoint data
        data_formatter: Formats data for different output requirements
    """
    
    # Required columns that must be present in input data
    REQUIRED_COLUMNS = {'thaiID', 'firstName', 'lastName', 'program', 'school'}
    
    def __init__(self):
        """Initialize the DataProcessor with all required components."""
        self.name_processor = NameProcessor()
        self.exam_assigner = ExamAssigner()
        self.checkpoint_manager = CheckpointManager()
        self.data_formatter = DataFormatter()
    
    def preprocess_data(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Preprocess the data by cleaning and formatting.
        
        Args:
            df: DataFrame with initial student data
            
        Returns:
            Optional[pd.DataFrame]: Preprocessed DataFrame or None if preprocessing failed
        
        Raises:
            ValueError: If the input DataFrame is missing required columns
        """
        # Validate input data first
        if df is None or df.empty:
            self._log_error("data preprocessing", ValueError("Input DataFrame is empty or None"))
            return None
            
        # Check for required columns
        self._validate_required_columns(df)
        
        try:
            df = self._apply_name_processing(df)
            return df
        except Exception as e:
            self._log_error("data preprocessing", e)
            return None
    
    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """
        Validate that the DataFrame contains all required columns.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If required columns are missing
        """
        missing_columns = self.REQUIRED_COLUMNS - set(df.columns)
        if missing_columns:
            error_msg = f"Input data is missing required columns: {missing_columns}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _apply_name_processing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply name processing steps to the data.
        
        Args:
            df: DataFrame with initial student data
            
        Returns:
            pd.DataFrame: DataFrame with processed names
        """
        df = self.name_processor.clean_school_names(df)
        df = self.name_processor.format_student_names(df)
        df = self.name_processor.school_name_correction(df)
        return df
    
    def _log_error(self, process_name: str, error: Exception) -> None:
        """
        Log an error with a standardized format including stack trace.
        
        Args:
            process_name: Name of the process where the error occurred
            error: The exception that was caught
        """
        logger.error(f"Error in {process_name}: {str(error)}")
        logger.debug(f"Traceback: {traceback.format_exc()}")
    
    def _load_checkpoint_data(self, checkpoint_file: Optional[str]) -> Dict:
        """
        Load checkpoint data if a checkpoint file is provided.
        
        Args:
            checkpoint_file: Path to the checkpoint file
            
        Returns:
            Dict: Dictionary with checkpoint data, empty if no file provided
        """
        checkpoint_data = {}
        if checkpoint_file:
            logger.info(f"Loading checkpoint data from {checkpoint_file}")
            checkpoint_data = self.checkpoint_manager.load_checkpoint(checkpoint_file)
        return checkpoint_data
    
    def _save_checkpoint_data(self, df: pd.DataFrame, checkpoint_file: Optional[str]) -> None:
        """
        Save checkpoint data if a checkpoint file is provided.
        
        Args:
            df: DataFrame with processed data
            checkpoint_file: Path to the checkpoint file
        """
        if checkpoint_file:
            logger.info(f"Saving checkpoint data to {checkpoint_file}")
            result = self.checkpoint_manager.save_checkpoint(df, checkpoint_file)
            if result:
                logger.info("Checkpoint data saved successfully")
            else:
                logger.warning("Failed to save checkpoint data")
    
    def _assign_exam_details(self, df: pd.DataFrame, checkpoint_data: Dict) -> Optional[pd.DataFrame]:
        """
        Assign exam details to students.
        
        Args:
            df: DataFrame with student data
            checkpoint_data: Dictionary with checkpoint data
            
        Returns:
            Optional[pd.DataFrame]: DataFrame with assigned exam details or None if assignment failed
        """
        logger.info(f"Assigning exam details to {len(df)} student records")
        return self.exam_assigner.assign_exam_details(df, checkpoint_data)
    
    def _execute_processing_pipeline(
        self, 
        df: pd.DataFrame, 
        checkpoint_file: Optional[str],
        formatter_func: Callable[[pd.DataFrame], Any],
        error_context: str
    ) -> Optional[Any]:
        """
        Execute the main data processing pipeline.
        
        Args:
            df: DataFrame with initial student data
            checkpoint_file: Optional path to a CSV file to store/load checkpoint data
            formatter_func: Function to format the final data
            error_context: Context for error logging
            
        Returns:
            Optional[Any]: Processed data in the format returned by formatter_func or None if processing failed
        """
        try:
            logger.info(f"Starting {error_context} pipeline with {len(df)} records")
            
            # Step 1: Preprocess the data
            processed_df = self.preprocess_data(df)
            if processed_df is None:
                logger.error(f"Preprocessing failed in {error_context} pipeline")
                return None
            
            # Step 2: Load checkpoint data if provided
            checkpoint_data = self._load_checkpoint_data(checkpoint_file)
            
            # Step 3: Assign exam details
            processed_df = self._assign_exam_details(processed_df, checkpoint_data)
            if processed_df is None:
                logger.error(f"Exam assignment failed in {error_context} pipeline")
                return None
            
            # Step 4: Save checkpoint data if provided
            self._save_checkpoint_data(processed_df, checkpoint_file)
            
            # Step 5: Format and return the data
            logger.info(f"Formatting data for output in {error_context} pipeline")
            result = formatter_func(processed_df)
            logger.info(f"Completed {error_context} pipeline successfully")
            return result
        except Exception as e:
            self._log_error(error_context, e)
            return None
    
    def process_data(self, df: pd.DataFrame, checkpoint_file: str = None) -> Optional[pd.DataFrame]:
        """
        Process the data through all processing steps.
        
        This method handles the full data processing workflow, including:
        - Name processing and cleaning
        - Loading checkpoint data if available
        - Assigning exam details
        - Saving checkpoint data
        - Formatting the final dataframe
        
        Args:
            df: DataFrame with initial student data
            checkpoint_file: Optional path to a CSV file to store/load checkpoint data
            
        Returns:
            Optional[pd.DataFrame]: Fully processed DataFrame or None if processing failed
        """
        return self._execute_processing_pipeline(
            df=df,
            checkpoint_file=checkpoint_file,
            formatter_func=self.data_formatter.prepare_final_dataframe,
            error_context="data processing"
        )
    
    def process_data_firebase(self, df: pd.DataFrame, checkpoint_file: str = None) -> Optional[List[Dict]]:
        """
        Process the data through all processing steps and return a dictionary for Firebase.
        
        This method follows the same workflow as process_data() but formats
        the output specifically for Firebase database upload.
        
        Args:
            df: DataFrame with initial student data
            checkpoint_file: Optional path to a CSV file to store/load checkpoint data

        Returns:
            Optional[List[Dict]]: List of dictionaries for Firebase or None if processing failed
        """
        return self._execute_processing_pipeline(
            df=df,
            checkpoint_file=checkpoint_file,
            formatter_func=self.data_formatter.format_for_firebase,
            error_context="data processing for Firebase"
        )

    def process_new_school_data_firebase(self, df: pd.DataFrame) -> Optional[List[Dict]]:
        """
        Process school data and return a dictionary for Firebase.
        
        This method handles a simplified workflow for updating school data:
        - Name processing and cleaning
        - Formatting the data for Firebase
        
        Args:
            df: DataFrame with initial student data

        Returns:
            Optional[List[Dict]]: List of dictionaries for Firebase or None if processing failed
        """
        try:
            logger.info(f"Starting school data processing with {len(df)} records")
            
            # Validate that required columns are present
            required_school_columns = {'thaiID', 'newSchool'}
            missing_columns = required_school_columns - set(df.columns)
            if missing_columns:
                error_msg = f"School data is missing required columns: {missing_columns}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Preprocess the data
            processed_df = self.preprocess_data(df)
            if processed_df is None:
                return None

            # Format for Firebase
            logger.info("Formatting school data for Firebase")
            result = self.data_formatter.format_school_data_for_firebase(processed_df)
            logger.info(f"Completed school data processing successfully with {len(result)} records")
            return result
        except Exception as e:
            self._log_error("school data processing for Firebase", e)
            return None
            
    def validate_output_data(self, data: Union[pd.DataFrame, List[Dict]]) -> bool:
        """
        Validate the processed output data.
        
        Args:
            data: The processed data to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        if data is None:
            logger.error("Output data validation failed: data is None")
            return False
            
        if isinstance(data, pd.DataFrame):
            if data.empty:
                logger.error("Output data validation failed: DataFrame is empty")
                return False
                
            # Check for key columns in DataFrame output
            required_columns = {'thaiID', 'program', 'exam_id', 'exam_room', 'exam_no'}
            missing_columns = required_columns - set(data.columns)
            if missing_columns:
                logger.error(f"Output data validation failed: Missing columns {missing_columns}")
                return False
        elif isinstance(data, list):
            if not data:
                logger.error("Output data validation failed: List is empty")
                return False
                
            # Check the first item for key fields if it's a list of dicts
            if data and isinstance(data[0], dict):
                # For exam data
                if 'examID' in data[0]:
                    required_keys = {'examID', 'examRoom', 'examNo'}
                    sample_record = data[0]
                    missing_keys = required_keys - set(sample_record.keys())
                    if missing_keys:
                        logger.error(f"Output data validation failed: Missing keys {missing_keys}")
                        return False
                # For school data
                elif 'thaiID' in data[0] and 'newSchool' in data[0]:
                    # Data structure is valid for school data
                    pass
                else:
                    logger.error("Output data validation failed: Unknown data format")
                    return False
                    
        logger.info("Output data validation passed")
        return True
            