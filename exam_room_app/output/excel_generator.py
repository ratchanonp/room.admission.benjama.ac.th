import pandas as pd
from pathlib import Path
from typing import Optional

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

class ExcelGenerator:
    """Class responsible for generating Excel output files."""
    
    def __init__(self, output_file: str = None):
        """
        Initialize the ExcelGenerator.
        
        Args:
            output_file: Path to the output Excel file
        """
        self.output_file = output_file or ExamRoomConfig.DEFAULT_EXCEL_OUTPUT
    
    def initialize_output_file(self) -> bool:
        """
        Initialize the output file by removing any existing file.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        try:
            # Remove existing output file if it exists
            if Path(self.output_file).exists():
                Path(self.output_file).unlink()
                logger.info(f"Removed existing output file: {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Error initializing output file: {str(e)}")
            return False
    
    def save_to_excel(self, df: pd.DataFrame, program: str) -> bool:
        """
        Save DataFrame to Excel with error handling, each program to a different sheet.
        
        Args:
            df: DataFrame to save
            program: Program ID string
            
        Returns:
            bool: True if save was successful, False otherwise
        """
        try:
            # Check if file exists to determine whether to create new or append
            if Path(self.output_file).exists():
                mode = 'a'
                if_sheet_exists = 'replace'
            else:
                mode = 'w'
                if_sheet_exists = None
            
            with pd.ExcelWriter(self.output_file, engine='openpyxl', mode=mode, if_sheet_exists=if_sheet_exists) as writer:
                # Save to sheet named after the program
                df.to_excel(writer, sheet_name=program, index=False)
                
                # Get the worksheet to adjust column widths
                worksheet = writer.sheets[program]
                
                # Set column widths
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(str(col))
                    ) + 2
                    # Limit maximum column width
                    max_length = min(max_length, 50)
                    # Convert character units to Excel units (approximate)
                    excel_width = max_length * 1.2
                    worksheet.column_dimensions[chr(65 + idx)].width = excel_width

            logger.info(f"Successfully saved program {program} to sheet in {self.output_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving program {program} to Excel {self.output_file}: {str(e)}")
            return False 