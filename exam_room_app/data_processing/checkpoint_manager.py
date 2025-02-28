import pandas as pd
import numpy as np
import os
import shutil
from typing import Dict, List, Tuple, Optional

from exam_room_app.utils.logger import logger

class CheckpointManager:
    """Class responsible for loading and saving checkpoint data."""
    
    # Constants for reuse
    REQUIRED_COLUMNS = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_no']
    CHECKPOINT_COLUMNS = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_no', 'exam_building', 'exam_floor']
    STRING_COLUMNS = ['thaiID', 'program', 'exam_id', 'exam_room', 'exam_building', 'exam_floor']
    
    def load_checkpoint(self, checkpoint_file: str) -> Dict:
        """
        Load checkpoint data from a CSV file.
        
        Args:
            checkpoint_file: Path to the checkpoint CSV file
            
        Returns:
            Dict: Dictionary with checkpoint data
        """
        checkpoint_data = {}
        
        if not self._is_valid_checkpoint_file(checkpoint_file):
            return checkpoint_data
            
        try:
            checkpoint_df = pd.read_csv(checkpoint_file)
            
            if not self._validate_checkpoint_columns(checkpoint_df, self.REQUIRED_COLUMNS):
                return checkpoint_data
            
            checkpoint_data = self._process_checkpoint_data(checkpoint_df)
            logger.info(f"Loaded {len(checkpoint_data)} checkpoint records from {checkpoint_file}")
            
        except Exception as e:
            logger.error(f"Error loading checkpoint data: {str(e)}")
            checkpoint_data = self._load_from_backup(checkpoint_file)
        
        return checkpoint_data
    
    def _is_valid_checkpoint_file(self, checkpoint_file: str) -> bool:
        """
        Check if the checkpoint file exists and is valid.
        
        Args:
            checkpoint_file: Path to the checkpoint file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        if not checkpoint_file or not os.path.exists(checkpoint_file):
            logger.info(f"No checkpoint file found at {checkpoint_file}")
            return False
        return True
    
    def _validate_checkpoint_columns(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Validate that the DataFrame contains all required columns.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            bool: True if all required columns exist, False otherwise
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"Checkpoint file is missing required columns: {missing_columns}. Continuing with empty checkpoint data.")
            return False
        return True
    
    def _process_checkpoint_data(self, df: pd.DataFrame) -> Dict:
        """
        Process checkpoint DataFrame into a dictionary.
        
        Args:
            df: DataFrame with checkpoint data
            
        Returns:
            Dict: Dictionary with processed checkpoint data
        """
        checkpoint_data = {}
        
        for _, row in df.iterrows():
            key = (str(row['thaiID']), str(row['program']))
            checkpoint_data[key] = {
                'exam_id': str(row['exam_id']),
                'exam_room': str(row['exam_room']),
                'exam_no': int(row['exam_no']),
                'exam_building': str(row.get('exam_building', 'ไม่ระบุ')),
                'exam_floor': str(row.get('exam_floor', 'ไม่ระบุ'))
            }
        
        return checkpoint_data
    
    def _load_from_backup(self, checkpoint_file: str) -> Dict:
        """
        Attempt to load data from backup checkpoint file.
        
        Args:
            checkpoint_file: Path to the original checkpoint file
            
        Returns:
            Dict: Dictionary with backup checkpoint data if available, empty dict otherwise
        """
        checkpoint_data = {}
        checkpoint_backup = f"{checkpoint_file}.bak"
        
        if not os.path.exists(checkpoint_backup):
            return checkpoint_data
            
        try:
            logger.info(f"Attempting to load checkpoint data from backup: {checkpoint_backup}")
            backup_df = pd.read_csv(checkpoint_backup)
            
            if not self._validate_checkpoint_columns(backup_df, self.REQUIRED_COLUMNS):
                return checkpoint_data
                
            checkpoint_data = self._process_checkpoint_data(backup_df)
            logger.info(f"Successfully loaded {len(checkpoint_data)} checkpoint records from backup")
            
        except Exception as backup_error:
            logger.error(f"Error loading checkpoint data from backup: {str(backup_error)}")
            
        return checkpoint_data
    
    def save_checkpoint(self, df: pd.DataFrame, checkpoint_file: str) -> bool:
        """
        Save checkpoint data to a CSV file.
        
        Args:
            df: DataFrame with student data
            checkpoint_file: Path to save the checkpoint CSV file
            
        Returns:
            bool: True if checkpoint was saved successfully, False otherwise
        """
        if not checkpoint_file:
            logger.warning("No checkpoint file path provided, skipping checkpoint save")
            return False
            
        try:
            if not self._validate_dataframe_columns(df, self.CHECKPOINT_COLUMNS):
                return False
            
            current_program_data = self._prepare_data_for_save(df)
            
            if os.path.exists(checkpoint_file):
                self._update_existing_checkpoint(current_program_data, checkpoint_file)
            else:
                self._create_new_checkpoint(current_program_data, checkpoint_file)
            
            return True
                
        except Exception as e:
            self._log_save_error(e, locals())
            return False
    
    def _validate_dataframe_columns(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Validate that the DataFrame contains all required columns for saving.
        
        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            
        Returns:
            bool: True if all required columns exist, False otherwise
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Cannot save checkpoint: Missing columns in data: {missing_columns}")
            raise ValueError(f"Missing required columns for checkpoint: {missing_columns}")
        return True
    
    def _prepare_data_for_save(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and prepare data for saving to checkpoint.
        
        Args:
            df: DataFrame with student data
            
        Returns:
            pd.DataFrame: Prepared data for saving
        """
        # Extract only the needed columns and create a copy
        return df[self.CHECKPOINT_COLUMNS].copy()
    
    def _normalize_dataframe_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data types in the DataFrame to avoid warnings and errors.
        
        Args:
            df: DataFrame to normalize
            
        Returns:
            pd.DataFrame: DataFrame with normalized types
        """
        df = df.copy()
        
        # Convert string columns
        for col in self.STRING_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype(str)
                df.loc[df[col] == 'nan', col] = ''
        
        # Handle numeric columns
        if 'exam_no' in df.columns:
            df['exam_no'] = df['exam_no'].replace([None, np.nan], 0)
            df['exam_no'] = df['exam_no'].astype(int)
            
        return df
    
    def _create_composite_key(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create a composite key for student identification.
        
        Args:
            df: DataFrame to add key to
            
        Returns:
            pd.DataFrame: DataFrame with added composite key
        """
        df = df.copy()
        df['key'] = df['thaiID'].astype(str) + '_' + df['program'].astype(str)
        return df
    
    def _create_backup(self, checkpoint_file: str) -> bool:
        """
        Create a backup of the checkpoint file.
        
        Args:
            checkpoint_file: Path to the checkpoint file
            
        Returns:
            bool: True if backup was created successfully, False otherwise
        """
        checkpoint_backup = f"{checkpoint_file}.bak"
        try:
            shutil.copy2(checkpoint_file, checkpoint_backup)
            logger.debug(f"Created backup of checkpoint file: {checkpoint_backup}")
            return True
        except Exception as backup_error:
            logger.warning(f"Failed to create backup of checkpoint file: {str(backup_error)}")
            return False
    
    def _update_existing_checkpoint(self, current_data: pd.DataFrame, checkpoint_file: str) -> None:
        """
        Update existing checkpoint file with new data.
        
        Args:
            current_data: DataFrame with new data
            checkpoint_file: Path to the checkpoint file
        """
        # Load existing checkpoint data
        existing_checkpoint = pd.read_csv(checkpoint_file)
        
        # Normalize data types
        existing_checkpoint = self._normalize_dataframe_types(existing_checkpoint)
        current_data = self._normalize_dataframe_types(current_data)
        
        # Create composite keys for merging
        existing_checkpoint = self._create_composite_key(existing_checkpoint)
        current_data = self._create_composite_key(current_data)
        
        # Remove rows from existing data that are being updated
        existing_keys = set(current_data['key'])
        existing_checkpoint = existing_checkpoint[~existing_checkpoint['key'].isin(existing_keys)]
        
        # Drop the temporary key column
        existing_checkpoint = existing_checkpoint.drop(columns=['key'])
        current_data = current_data.drop(columns=['key'])
        
        # Combine the data
        combined_data = pd.concat([existing_checkpoint, current_data], ignore_index=True)
        
        # Create backup before saving
        self._create_backup(checkpoint_file)
        
        # Save combined data
        combined_data.to_csv(checkpoint_file, index=False)
        logger.info(f"Updated checkpoint file with {len(current_data)} records, total records: {len(combined_data)}")
    
    def _create_new_checkpoint(self, data: pd.DataFrame, checkpoint_file: str) -> None:
        """
        Create a new checkpoint file.
        
        Args:
            data: DataFrame to save
            checkpoint_file: Path to the checkpoint file
        """
        data = self._normalize_dataframe_types(data)
        data.to_csv(checkpoint_file, index=False)
        logger.info(f"Created new checkpoint file with {len(data)} records")
    
    def _log_save_error(self, error: Exception, local_vars: Dict) -> None:
        """
        Log detailed information about errors during save.
        
        Args:
            error: The exception that occurred
            local_vars: Local variables at the time of the error
        """
        logger.error(f"Error saving checkpoint data: {str(error)}")
        
        try:
            # Log data types to help diagnose issues
            if 'current_program_data' in local_vars:
                logger.debug(f"Current program data types: {local_vars['current_program_data'].dtypes}")
            if 'existing_checkpoint' in local_vars:
                logger.debug(f"Existing checkpoint data types: {local_vars['existing_checkpoint'].dtypes}")
                
            logger.error(f"Checkpoint save error details: {type(error).__name__} - {str(error)}")
        except Exception as debug_error:
            logger.error(f"Error while trying to log debug info: {str(debug_error)}") 