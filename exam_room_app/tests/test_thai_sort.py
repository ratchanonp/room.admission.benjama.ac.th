import unittest
import pandas as pd

from exam_room_app.data_processing.data_processor import DataProcessor

class TestThaiSort(unittest.TestCase):
    """Tests for the Thai sorting functionality in DataProcessor."""
    
    def setUp(self):
        """Set up the test case."""
        self.processor = DataProcessor()
    
    def test_get_thai_sort_key(self):
        """Test the Thai sorting key function with different cases."""
        # Test with normal names (no leading vowels)
        self.assertEqual(self.processor._get_thai_sort_key("กมล"), "กมล")
        self.assertEqual(self.processor._get_thai_sort_key("ขวัญ"), "ขวัญ")
        
        # Test with leading vowels
        self.assertEqual(self.processor._get_thai_sort_key("เมธา"), "มเธา")
        self.assertEqual(self.processor._get_thai_sort_key("แสง"), "สแง")
        self.assertEqual(self.processor._get_thai_sort_key("โอม"), "อโม")
        
        # Test with edge cases
        self.assertEqual(self.processor._get_thai_sort_key(""), "")
        self.assertEqual(self.processor._get_thai_sort_key("ก"), "ก")
        self.assertEqual(self.processor._get_thai_sort_key("เก"), "กเ")
    
    def test_thai_name_sorting(self):
        """Test sorting a list of Thai names."""
        # Create a sample dataframe with Thai names
        data = {
            "firstname": ["กมล", "เมธา", "อรุณ", "แสง", "โอภาส", "ชัย", "ไตรรัตน์"],
            "lastname": ["จันทร์", "สุข", "พงษ์", "ไพศาล", "กมล", "เวช", "ทองคำ"]
        }
        df = pd.DataFrame(data)
        
        # Apply the sorting function
        df["firstname_sort_key"] = df["firstname"].apply(self.processor._get_thai_sort_key)
        df["lastname_sort_key"] = df["lastname"].apply(self.processor._get_thai_sort_key)
        sorted_df = df.sort_values(by=["firstname_sort_key", "lastname_sort_key"])
        
        # Expected order after sorting: กมล, ชัย, ไตรรัตน์, เมธา, แสง, โอภาส, อรุณ
        # This is because in Thai:
        # - กมล starts with ก
        # - ชัย starts with ช
        # - ไตรรัตน์ has ต as first consonant
        # - เมธา has ม as first consonant
        # - แสง has ส as first consonant
        # - โอภาส has อ as first consonant
        # - อรุณ starts with อ
        expected_order = ["กมล", "ชัย", "ไตรรัตน์", "เมธา", "แสง", "อรุณ", "โอภาส"]
        
        self.assertEqual(sorted_df["firstname"].tolist(), expected_order)
    
    def test_assign_exam_details_sorting(self):
        """Test sorting in the assign_exam_details method."""
        # Create a sample dataframe for a simple program
        data = {
            "firstname": ["เมธา", "กมล", "แสง"],
            "lastname": ["สุข", "จันทร์", "ไพศาล"],
            "program": ["test-program"] * 3,
            "thaiID": ["1111111111111", "2222222222222", "3333333333333"],
            "title": ["นาย", "นาย", "นาย"],
            "school": ["School A", "School B", "School C"]
        }
        df = pd.DataFrame(data)
        
        # Mock the exam_rooms attribute with test data
        self.processor.exam_rooms = {
            "test-program": [("TestRoom", 10)]
        }
        self.processor.exam_id_prefix = {
            "test-program": "99"
        }
        self.processor.room_metadata = {
            "TestRoom": {"building": "Test Building", "floor": "1"}
        }
        
        # Process the data without checkpoint file
        result_df = self.processor.assign_exam_details(df, checkpoint_file=None)
        
        # Verify the sort order (by exam_no which indicates the order they were processed)
        # กมล should be first, เมธา second, and แสง third
        expected_order = {
            "1111111111111": 2,  # เมธา
            "2222222222222": 1,  # กมล
            "3333333333333": 3,  # แสง
        }
        
        for thai_id, expected_exam_no in expected_order.items():
            actual_exam_no = result_df[result_df["thaiID"] == thai_id]["exam_no"].values[0]
            self.assertEqual(actual_exam_no, expected_exam_no)

    def test_checkpoint_functionality(self):
        """Test that the checkpoint functionality prevents reassignment of rooms."""
        import tempfile
        import os
        
        # Create a sample dataframe for a simple program
        data = {
            "firstname": ["เมธา", "กมล", "แสง"],
            "lastname": ["สุข", "จันทร์", "ไพศาล"],
            "program": ["test-program"] * 3,
            "thaiID": ["1111111111111", "2222222222222", "3333333333333"],
            "title": ["นาย", "นาย", "นาย"],
            "school": ["School A", "School B", "School C"]
        }
        df = pd.DataFrame(data)
        
        # Mock the exam_rooms attribute with test data
        self.processor.exam_rooms = {
            "test-program": [("TestRoom", 10)]
        }
        self.processor.exam_id_prefix = {
            "test-program": "99"
        }
        self.processor.room_metadata = {
            "TestRoom": {"building": "Test Building", "floor": "1"}
        }
        
        # Create a temporary checkpoint file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            checkpoint_file = temp_file.name
        
        try:
            # First run - assign rooms and save to checkpoint
            first_result = self.processor.assign_exam_details(df, checkpoint_file=checkpoint_file)
            
            # Record the initial assignments
            initial_assignments = {}
            for _, row in first_result.iterrows():
                initial_assignments[row['thaiID']] = {
                    'exam_room': row['exam_room'],
                    'exam_no': row['exam_no']
                }
            
            # Create a new dataframe with the same students but different order
            # This would normally cause different assignments without the checkpoint
            data2 = {
                "firstname": ["แสง", "เมธา", "กมล"],  # Different order
                "lastname": ["ไพศาล", "สุข", "จันทร์"],
                "program": ["test-program"] * 3,
                "thaiID": ["3333333333333", "1111111111111", "2222222222222"],  # Same IDs
                "title": ["นาย", "นาย", "นาย"],
                "school": ["School C", "School A", "School B"]
            }
            df2 = pd.DataFrame(data2)
            
            # Second run - should use checkpoint data
            second_result = self.processor.assign_exam_details(df2, checkpoint_file=checkpoint_file)
            
            # Verify that assignments remain the same despite different order
            for thai_id, initial in initial_assignments.items():
                second_assignment = second_result[second_result['thaiID'] == thai_id]
                self.assertEqual(
                    second_assignment['exam_room'].values[0], 
                    initial['exam_room'],
                    f"Room assignment changed for student {thai_id}"
                )
                self.assertEqual(
                    second_assignment['exam_no'].values[0], 
                    initial['exam_no'],
                    f"Seat number changed for student {thai_id}"
                )
                
            # Add a new student to the dataframe
            data3 = {
                "firstname": ["ใหม่"],  # New student
                "lastname": ["ทดสอบ"],
                "program": ["test-program"],
                "thaiID": ["4444444444444"],  # New ID
                "title": ["นาย"],
                "school": ["School D"]
            }
            df3 = pd.concat([df2, pd.DataFrame(data3)])
            
            # Third run - should use checkpoint data for existing students and assign new student
            third_result = self.processor.assign_exam_details(df3, checkpoint_file=checkpoint_file)
            
            # Verify existing students keep their assignments
            for thai_id, initial in initial_assignments.items():
                third_assignment = third_result[third_result['thaiID'] == thai_id]
                self.assertEqual(
                    third_assignment['exam_room'].values[0], 
                    initial['exam_room'],
                    f"Room assignment changed for student {thai_id} after adding new student"
                )
                self.assertEqual(
                    third_assignment['exam_no'].values[0], 
                    initial['exam_no'],
                    f"Seat number changed for student {thai_id} after adding new student"
                )
            
            # Verify new student got assigned
            new_student = third_result[third_result['thaiID'] == "4444444444444"]
            self.assertNotEqual(new_student['exam_room'].values[0], "")
            self.assertNotEqual(new_student['exam_no'].values[0], 0)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(checkpoint_file):
                os.unlink(checkpoint_file)

    def test_checkpoint_functionality_multiple_programs(self):
        """Test that the checkpoint functionality works with multiple programs sharing the same file."""
        import tempfile
        import os
        
        # Create a temporary checkpoint file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            checkpoint_file = temp_file.name
        
        try:
            # Configure test data for the first program
            self.processor.exam_rooms = {
                "test-program-1": [("Room1", 10)],
                "test-program-2": [("Room2", 10)]
            }
            self.processor.exam_id_prefix = {
                "test-program-1": "11",
                "test-program-2": "22"
            }
            self.processor.room_metadata = {
                "Room1": {"building": "Building 1", "floor": "1"},
                "Room2": {"building": "Building 2", "floor": "2"}
            }
            
            # Create data for first program
            data1 = {
                "firstname": ["เมธา", "กมล"],
                "lastname": ["สุข", "จันทร์"],
                "program": ["test-program-1"] * 2,
                "thaiID": ["1111111111111", "2222222222222"],
                "title": ["นาย", "นาย"],
                "school": ["School A", "School B"]
            }
            df1 = pd.DataFrame(data1)
            
            # Process the first program
            result1 = self.processor.assign_exam_details(df1, checkpoint_file=checkpoint_file)
            
            # Create data for second program
            data2 = {
                "firstname": ["แสง", "ใหม่"],
                "lastname": ["ไพศาล", "ทดสอบ"],
                "program": ["test-program-2"] * 2,
                "thaiID": ["3333333333333", "4444444444444"],
                "title": ["นาย", "นาย"],
                "school": ["School C", "School D"]
            }
            df2 = pd.DataFrame(data2)
            
            # Process the second program
            result2 = self.processor.assign_exam_details(df2, checkpoint_file=checkpoint_file)
            
            # Load the checkpoint file and verify it contains all four students
            checkpoint_df = pd.read_csv(checkpoint_file)
            self.assertEqual(len(checkpoint_df), 4)
            
            # Verify each program's students are in the checkpoint
            program1_students = checkpoint_df[checkpoint_df['program'] == 'test-program-1']
            program2_students = checkpoint_df[checkpoint_df['program'] == 'test-program-2']
            self.assertEqual(len(program1_students), 2)
            self.assertEqual(len(program2_students), 2)
            
            # Check if each thaiID is present
            for thai_id in ["1111111111111", "2222222222222", "3333333333333", "4444444444444"]:
                self.assertTrue(thai_id in checkpoint_df['thaiID'].values, f"Thai ID {thai_id} missing from checkpoint")
            
            # Now create a mixed dataframe with students from both programs but in different order
            data3 = {
                "firstname": ["แสง", "เมธา", "กมล", "ใหม่"],
                "lastname": ["ไพศาล", "สุข", "จันทร์", "ทดสอบ"],
                "program": ["test-program-2", "test-program-1", "test-program-1", "test-program-2"],
                "thaiID": ["3333333333333", "1111111111111", "2222222222222", "4444444444444"],
                "title": ["นาย", "นาย", "นาย", "นาย"],
                "school": ["School X", "School Y", "School Z", "School W"]  # Changed schools
            }
            df3 = pd.DataFrame(data3)
            
            # Process the mixed data - should preserve existing room assignments
            result3 = self.processor.assign_exam_details(df3, checkpoint_file=checkpoint_file)
            
            # Verify that all assignments remain the same
            for i, thai_id in enumerate(["3333333333333", "1111111111111", "2222222222222", "4444444444444"]):
                # Get the original results based on the program
                original_program = data3["program"][i]
                original_result = result1 if original_program == "test-program-1" else result2
                original_row = original_result[original_result["thaiID"] == thai_id]
                
                # Get the new result
                new_row = result3[result3["thaiID"] == thai_id]
                
                # Verify room and number remained the same
                self.assertEqual(
                    new_row['exam_room'].values[0], 
                    original_row['exam_room'].values[0],
                    f"Room assignment changed for student {thai_id}"
                )
                self.assertEqual(
                    new_row['exam_no'].values[0], 
                    original_row['exam_no'].values[0],
                    f"Seat number changed for student {thai_id}"
                )
                
            # Add a completely new student
            data4 = {
                "firstname": ["นิสิต"],
                "lastname": ["ใหม่"],
                "program": ["test-program-1"],
                "thaiID": ["5555555555555"],
                "title": ["นาย"],
                "school": ["School E"]
            }
            df4 = pd.concat([df3, pd.DataFrame(data4)])
            
            # Process with the new student
            result4 = self.processor.assign_exam_details(df4, checkpoint_file=checkpoint_file)
            
            # Verify checkpoint now has 5 students
            updated_checkpoint = pd.read_csv(checkpoint_file)
            self.assertEqual(len(updated_checkpoint), 5)
            
            # Check if the new student got assigned a room and is in the checkpoint
            self.assertTrue("5555555555555" in updated_checkpoint['thaiID'].values)
            new_student = result4[result4['thaiID'] == "5555555555555"]
            self.assertNotEqual(new_student['exam_room'].values[0], "")
            self.assertNotEqual(new_student['exam_no'].values[0], 0)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(checkpoint_file):
                os.unlink(checkpoint_file)

if __name__ == "__main__":
    unittest.main() 