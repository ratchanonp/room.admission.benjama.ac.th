import argparse
import sys

from exam_room_app.app import ExamRoomApplication
from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate exam room assignments.')
    
    parser.add_argument(
        '--input-file', 
        type=str, 
        default=ExamRoomConfig.EXCEL_INPUT_FILE,
        help=f'Path to the input Excel file (default: {ExamRoomConfig.EXCEL_INPUT_FILE})'
    )
    
    parser.add_argument(
        '--sheet-name', 
        type=str, 
        default=ExamRoomConfig.SHEET_NAME,
        help=f'Name of the sheet to process (default: {ExamRoomConfig.SHEET_NAME})'
    )
    
    parser.add_argument(
        '--output-excel', 
        type=str, 
        default=ExamRoomConfig.DEFAULT_EXCEL_OUTPUT,
        help=f'Path to the output Excel file (default: {ExamRoomConfig.DEFAULT_EXCEL_OUTPUT})'
    )
    
    # Checkpoint file parameter
    parser.add_argument(
        '--checkpoint-file', 
        type=str, 
        default=ExamRoomConfig.DEFAULT_CHECKPOINT_FILE,
        help=f'Path to a CSV file to store/load checkpoint data (default: {ExamRoomConfig.DEFAULT_CHECKPOINT_FILE})'
    )
    
    # Firebase control parameters
    parser.add_argument(
        '--no-firebase',
        action='store_true',
        help='Disable all Firebase operations'
    )
    
    parser.add_argument(
        '--no-firebase-exam',
        action='store_true',
        help='Disable writing exam room data to Firebase'
    )
    
    parser.add_argument(
        '--no-firebase-school',
        action='store_true',
        help='Disable writing school data to Firebase'
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Create and run the application
        app = ExamRoomApplication(
            input_file=args.input_file,
            sheet_name=args.sheet_name,
            output_excel=args.output_excel,
            use_firebase=not args.no_firebase,
            use_firebase_exam=not args.no_firebase_exam,
            use_firebase_school=not args.no_firebase_school,
            checkpoint_file=args.checkpoint_file
        )
        
        # Run the application
        success = app.run()
        
        # Exit with appropriate status code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 