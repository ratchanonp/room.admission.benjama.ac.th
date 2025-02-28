import pandas as pd
from typing import List, Optional
from pathlib import Path

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.data_processing.data_loader import DataLoader
from exam_room_app.data_processing.data_processor import DataProcessor
from exam_room_app.output.excel_generator import ExcelGenerator
from exam_room_app.output.firebase import Firebase
from exam_room_app.output.pdf_generator import PDFGenerator
from exam_room_app.utils.logger import logger

class ExamRoomApplication:
    """Main application class that orchestrates the exam room assignment process."""
    
    def __init__(self, input_file: str = None, sheet_name: str = None, output_excel: str = None, 
                 use_firebase: bool = True, use_firebase_exam: bool = True, use_firebase_school: bool = True,
                 checkpoint_file: str = None):
        """
        Initialize the ExamRoomApplication.
        
        Args:
            input_file: Path to the input Excel file
            sheet_name: Name of the sheet to process
            output_excel: Path to the output Excel file
            use_firebase: Whether to write any data to Firebase (default: True)
            use_firebase_exam: Whether to write exam room data to Firebase (default: True)
            use_firebase_school: Whether to write school data to Firebase (default: True)
            checkpoint_file: Path to a CSV file to store/load checkpoint data (default: None)
        """
        self.data_loader = DataLoader(input_file, sheet_name)
        self.data_processor = DataProcessor()
        self.excel_generator = ExcelGenerator(output_excel)
        self.pdf_generator = PDFGenerator()
        self.program_ids = list(ExamRoomConfig.EXAM_ID_PREFIX.keys())
        self.checkpoint_file = checkpoint_file
        
        # Master switch for Firebase
        self.use_firebase = use_firebase
        
        # Individual controls for Firebase operations
        self.use_firebase_exam = use_firebase_exam and use_firebase
        self.use_firebase_school = use_firebase_school and use_firebase
        
        # Only initialize Firebase if at least one operation is enabled
        self.firebase = Firebase() if (self.use_firebase_exam or self.use_firebase_school) else None
    def run(self) -> bool:
        """
        Run the complete exam room assignment process.
        
        Returns:
            bool: True if process completed successfully, False otherwise
        """
        logger.info("Starting exam room assignment process")
        
        try:
            # Initialize output file
            if not self.excel_generator.initialize_output_file():
                logger.error("Failed to initialize output file")
                return False
            
            # Load and process data
            data = self.data_loader.load_data()
            if data is None:
                logger.error("Failed to load input data")
                return False
            
            # Track success for each program
            overall_success = True
            
            # Process each program
            for program in self.program_ids:
                try:
                    program_data = data[data["program"] == program]
                    if len(program_data) == 0:
                        logger.info(f"No students found for program {program}")
                        continue
                    
                    # Process the data
                    logger.info(f"Processing program {program} with {len(program_data)} students")
                    
                    processed_data = self.process_program_data(program_data)
                    if processed_data is None:
                        logger.error(f"Failed to process program {program}")
                        overall_success = False
                        continue
                    
                    # Save to Excel
                    if not self.excel_generator.save_to_excel(processed_data, program):
                        logger.error(f"Failed to save Excel for program {program}")
                        overall_success = False
                    
                    # Generate PDF
                    if not self.pdf_generator.create_pdf_file(processed_data, program):
                        logger.error(f"Failed to create PDF for program {program}")
                        overall_success = False

                    # Handle Firebase exam room data operation
                    if self.use_firebase_exam:
                        firebase_data = self.process_program_data_firebase(program_data)    
                        if firebase_data is None:
                            logger.error(f"Failed to process program {program} for Firebase exam data")
                            overall_success = False
                            continue
                        if not self.firebase.set_exam_room_data(firebase_data):
                            logger.error(f"Failed to save exam room data to Firebase for program {program}")
                            overall_success = False
                    else:
                        logger.info(f"Skipping Firebase exam room data operations for program {program} as requested")
                    
                    # Handle Firebase school data operation
                    if self.use_firebase_school:
                        firebase_data = self.process_new_school_data_firebase(program_data)    
                        if firebase_data is None:
                            logger.error(f"Failed to process program {program} for Firebase school data")
                            overall_success = False
                            continue
                        if not self.firebase.set_new_school_data(firebase_data):
                            logger.error(f"Failed to save school data to Firebase for program {program}")
                            overall_success = False
                    else:
                        logger.info(f"Skipping Firebase school data operations for program {program} as requested")
                
                except Exception as e:
                    logger.error(f"Error processing program {program}: {str(e)}")
                    overall_success = False
                    continue
            
            logger.info("Exam room assignment process completed")
            return overall_success
            
        except Exception as e:
            logger.error(f"Critical error in main process: {str(e)}")
            return False
    
    def process_program_data(self, program_data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Process data for a specific program.
        
        Args:
            program_data: DataFrame containing data for a specific program
            
        Returns:
            Optional[pd.DataFrame]: Processed DataFrame or None if processing failed
        """
        try:
            return self.data_processor.process_data(program_data, self.checkpoint_file)
        except Exception as e:
            logger.error(f"Error in program data processing: {str(e)}")
            return None 
        
    def process_program_data_firebase(self, program_data: pd.DataFrame) -> Optional[dict]:
        """
        Process data for a specific program and return a dictionary for Firebase.
        """
        try:
            return self.data_processor.process_data_firebase(program_data, self.checkpoint_file)
        except Exception as e:
            logger.error(f"Error in program data processing for Firebase: {str(e)}")
            return None

    def process_new_school_data_firebase(self, program_data: pd.DataFrame) -> Optional[dict]:
        """
        Process data for a specific program and return a dictionary for Firebase.
        """
        try:
            return self.data_processor.process_new_school_data_firebase(program_data)
        except Exception as e:
            logger.error(f"Error in program data processing for Firebase: {str(e)}")
            return None