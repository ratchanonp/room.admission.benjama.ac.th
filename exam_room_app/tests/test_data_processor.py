import unittest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from exam_room_app.data_processing import (
    DataProcessor, 
    NameProcessor, 
    ExamAssigner, 
    CheckpointManager, 
    DataFormatter
)

class TestDataProcessor(unittest.TestCase):
    """Test cases for the refactored DataProcessor class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a sample dataframe
        self.sample_data = pd.DataFrame({
            'thaiID': ['1234567890123', '2345678901234'],
            'title': ['นาย', 'นางสาว'],
            'firstname': ['ทดสอบ', 'เทสติ้ง'],
            'lastname': ['การทำงาน', 'นะครับ'],
            'school': ['โรงเรียนทดสอบ', 'วิทยาลัยการทดสอบ'],
            'program': ['A', 'B']
        })
        
        # Create a temporary directory for checkpoint files
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """Test that the DataProcessor initializes correctly with all components."""
        processor = DataProcessor()
        self.assertIsInstance(processor.name_processor, NameProcessor)
        self.assertIsInstance(processor.exam_assigner, ExamAssigner)
        self.assertIsInstance(processor.checkpoint_manager, CheckpointManager)
        self.assertIsInstance(processor.data_formatter, DataFormatter)
    
    @patch('exam_room_app.data_processing.name_processor.NameProcessor.clean_school_names')
    @patch('exam_room_app.data_processing.name_processor.NameProcessor.format_student_names')
    @patch('exam_room_app.data_processing.name_processor.NameProcessor.school_name_correction')
    def test_preprocess_data(self, mock_school_correction, mock_format_names, mock_clean_schools):
        """Test that preprocess_data calls the correct methods from NameProcessor."""
        # Set up mock returns
        mock_clean_schools.return_value = self.sample_data
        mock_format_names.return_value = self.sample_data
        mock_school_correction.return_value = self.sample_data
        
        processor = DataProcessor()
        result = processor.preprocess_data(self.sample_data)
        
        # Verify all methods were called with the correct data
        mock_clean_schools.assert_called_once()
        mock_format_names.assert_called_once()
        mock_school_correction.assert_called_once()
        
        # Verify we got the expected result
        self.assertIs(result, self.sample_data)
        
    @patch('exam_room_app.data_processing.exam_assigner.ExamAssigner.assign_exam_details')
    def test_process_data(self, mock_assign_exam):
        """Test that process_data calls the correct methods."""
        # Create a DataProcessor with mocked components
        processor = DataProcessor()
        processor.preprocess_data = MagicMock(return_value=self.sample_data)
        processor.checkpoint_manager.load_checkpoint = MagicMock(return_value={})
        processor.checkpoint_manager.save_checkpoint = MagicMock(return_value=True)
        processor.data_formatter.prepare_final_dataframe = MagicMock(return_value=self.sample_data)
        
        # Set up mock return for assign_exam_details
        mock_assign_exam.return_value = self.sample_data
        
        # Call process_data with a checkpoint file
        checkpoint_file = os.path.join(self.test_dir, 'checkpoint.csv')
        result = processor.process_data(self.sample_data, checkpoint_file)
        
        # Verify all methods were called correctly
        processor.preprocess_data.assert_called_once_with(self.sample_data)
        processor.checkpoint_manager.load_checkpoint.assert_called_once_with(checkpoint_file)
        mock_assign_exam.assert_called_once()
        processor.checkpoint_manager.save_checkpoint.assert_called_once()
        processor.data_formatter.prepare_final_dataframe.assert_called_once_with(self.sample_data)
        
        # Verify we got the expected result
        self.assertIs(result, self.sample_data)
        
    def test_process_data_firebase(self):
        """Test that process_data_firebase calls the correct methods."""
        # Create a DataProcessor with mocked components
        processor = DataProcessor()
        processor.preprocess_data = MagicMock(return_value=self.sample_data)
        processor.checkpoint_manager.load_checkpoint = MagicMock(return_value={})
        processor.checkpoint_manager.save_checkpoint = MagicMock(return_value=True)
        processor.exam_assigner.assign_exam_details = MagicMock(return_value=self.sample_data)
        processor.data_formatter.format_for_firebase = MagicMock(return_value=[{'examID': '001'}])
        
        # Call process_data_firebase with a checkpoint file
        checkpoint_file = os.path.join(self.test_dir, 'checkpoint.csv')
        result = processor.process_data_firebase(self.sample_data, checkpoint_file)
        
        # Verify all methods were called correctly
        processor.preprocess_data.assert_called_once_with(self.sample_data)
        processor.checkpoint_manager.load_checkpoint.assert_called_once_with(checkpoint_file)
        processor.exam_assigner.assign_exam_details.assert_called_once()
        processor.checkpoint_manager.save_checkpoint.assert_called_once()
        processor.data_formatter.format_for_firebase.assert_called_once_with(self.sample_data)
        
        # Verify we got the expected result
        self.assertEqual(result, [{'examID': '001'}])
        
    def test_process_new_school_data_firebase(self):
        """Test that process_new_school_data_firebase calls the correct methods."""
        # Create a DataProcessor with mocked components
        processor = DataProcessor()
        processor.preprocess_data = MagicMock(return_value=self.sample_data)
        processor.data_formatter.format_school_data_for_firebase = MagicMock(return_value=[{'thaiID': '1234567890123', 'newSchool': 'ทดสอบ'}])
        
        # Call process_new_school_data_firebase
        result = processor.process_new_school_data_firebase(self.sample_data)
        
        # Verify all methods were called correctly
        processor.preprocess_data.assert_called_once_with(self.sample_data)
        processor.data_formatter.format_school_data_for_firebase.assert_called_once_with(self.sample_data)
        
        # Verify we got the expected result
        self.assertEqual(result, [{'thaiID': '1234567890123', 'newSchool': 'ทดสอบ'}])

if __name__ == '__main__':
    unittest.main() 