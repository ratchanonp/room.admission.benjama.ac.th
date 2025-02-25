import pandas as pd
from fpdf import FPDF
from typing import List, Tuple, Set, Optional
from pathlib import Path

from exam_room_app.config.constants import ExamRoomConfig
from exam_room_app.utils.logger import logger

class PDFGenerator:
    """Class responsible for generating PDF output files."""
    
    def __init__(self):
        """Initialize the PDFGenerator."""
        self.exam_rooms = ExamRoomConfig.EXAM_ROOMS
        self.program_thai_name = ExamRoomConfig.PROGRAM_THAI_NAME
        self.academic_year = ExamRoomConfig.ACADEMIC_YEAR
        self.m1_exam_date = ExamRoomConfig.M1_EXAM_DATE
        self.m4_exam_date = ExamRoomConfig.M4_EXAM_DATE
        self.font_regular = ExamRoomConfig.FONT_REGULAR
        self.font_bold = ExamRoomConfig.FONT_BOLD
        self.pdf_output_template = ExamRoomConfig.PDF_OUTPUT_TEMPLATE
    
    def get_optimal_font_size(self, pdf: FPDF, text: str, width: float, min_size: int = 4, max_size: int = 14) -> int:
        """
        Calculate the optimal font size for text to fit in width.
        
        Args:
            pdf: FPDF instance
            text: Text to calculate size for
            width: Available width
            min_size: Minimum font size
            max_size: Maximum font size
            
        Returns:
            int: Optimal font size
        """
        if not text:
            return max_size
                
        # Start with the maximum size
        for font_size in range(max_size, min_size - 1, -1):
            pdf.set_font('thsarabun', '', font_size)
            text_width = pdf.get_string_width(str(text))
            if text_width <= width - 2:  # 2mm padding
                return font_size
        
        # If we get here, even the smallest font size is too large, return min size
        return min_size
    
    def create_pdf_file(self, df: pd.DataFrame, program: str) -> bool:
        """
        Create a PDF file with exam room assignments for a specific program.
        
        Args:
            df: DataFrame containing exam room assignments
            program: Program ID string
            
        Returns:
            bool: True if successful, False otherwise
        """
        output_file = self.pdf_output_template.format(program)
        
        try:
            # Initialize PDF
            pdf = FPDF(orientation='portrait', format='A4')  # Portrait orientation
            
            # Check if font files exist
            font_path = Path(self.font_regular)
            font_bold_path = Path(self.font_bold)
            
            if not font_path.exists() or not font_bold_path.exists():
                logger.error(f"Font files not found: {self.font_regular} or {self.font_bold}")
                return False
                
            pdf.add_font('thsarabun', '', self.font_regular)
            pdf.add_font('thsarabun', 'B', self.font_bold)
            
            # Get rooms in the order defined in EXAM_ROOMS
            if program not in self.exam_rooms:
                logger.error(f"No room configuration found for program: {program}")
                return False
                
            # Get all rooms for this program in their original order
            program_room_list = [room_name for room_name, _ in self.exam_rooms[program]]
            
            # Get rooms that actually have students (may be a subset of all rooms)
            actual_rooms = set(df['ห้องสอบ'].unique())
            
            # Filter and keep only rooms that have students, maintaining original order
            ordered_rooms = [room for room in program_room_list if room in actual_rooms]
            
            if not ordered_rooms:
                logger.error(f"No matching rooms found for program {program}")
                return False
                
            total_pages = len(ordered_rooms)
            
            # Process each room in the order from EXAM_ROOMS
            for room_idx, room in enumerate(ordered_rooms, 1):
                room_data = df[df['ห้องสอบ'] == room].copy()
                room_data = room_data.sort_values('เลขที่นั่งสอบ')
                
                # Add a new page for each room
                pdf.add_page()
                
                # Page number
                pdf.set_font('thsarabun', 'B', 10)
                pdf.cell(0, 4, f'แผ่นที่ {room_idx}/{total_pages}', align='R', ln=True)
                
                # Headers with fixed font sizes and heights
                pdf.set_font('thsarabun', 'B', 14)
                pdf.cell(0, 6, 'ใบรายชื่อผู้เข้าสอบ', align='C', ln=True)
                pdf.cell(0, 6, 'การสอบคัดเลือกเข้าศึกษาต่อชั้นมัธยมศึกษาปีที่ ' + ('4' if program.startswith('m4') else '1'), align='C', ln=True)
                
                # Handle long program names by wrapping text
                pdf.set_font('thsarabun', '', 12)
                program_name = self.program_thai_name[program]
                
                # Calculate available width (A4 width - margins)
                available_width = 190  # mm
                
                # Split text into lines that fit the width
                pdf.set_x(10)  # Reset X position
                lines = []
                current_line = ""
                words = program_name.split()
                
                for word in words:
                    test_line = current_line + (" " if current_line else "") + word
                    if pdf.get_string_width(test_line) <= available_width:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
                
                # Output each line centered
                for line in lines:
                    pdf.cell(0, 5, line, align='C', ln=True)
                
                pdf.set_font('thsarabun', '', 12)
                pdf.cell(0, 5, f'ปีการศึกษา {self.academic_year} โรงเรียนเบญจมราชูทิศ', align='C', ln=True)
                exam_date = self.m1_exam_date if program.startswith('m1') else self.m4_exam_date
                pdf.cell(0, 5, f'วันที่ {exam_date} ห้องสอบที่ {room_idx} ห้อง {room}', align='C', ln=True)
                
                # Define exact column widths - carefully tuned to fit portrait page
                # Ensure these add up to PDF page width minus margins
                # A4 width is 210mm minus left and right margin (~20mm total)
                headers = ['เลขที่นั่งสอบ', 'เลขประจำตัวสอบ', 'ชื่อ - นามสกุล', 'โรงเรียน', 'ลงชื่อผู้เข้าสอบ', 'หมายเหตุ']
                col_widths = [20, 20, 50, 50, 35, 20]  # Total = 195mm
                
                # Calculate start X position to center the table
                page_width = 210
                table_width = sum(col_widths)
                start_x = (page_width - table_width) / 2
                
                # Set start position with fixed spacing
                pdf.ln(2)
                pdf.set_x(start_x)
                
                # Draw table header with fixed height and font
                header_start_x = pdf.get_x()
                
                # Fixed header row height
                header_height = 6
                
                # Draw each header with appropriate font size
                current_x = header_start_x
                for i, (width, header) in enumerate(zip(col_widths, headers)):
                    # Set position for this header cell
                    pdf.set_xy(current_x, pdf.get_y())
                    
                    # Set different font sizes based on the header content
                    if header in ['เลขที่นั่งสอบ', 'เลขประจำตัวสอบ']:
                        # Smaller font size for exam number headers
                        pdf.set_font('thsarabun', 'B', 10)
                    else:
                        # Regular font size for other headers
                        pdf.set_font('thsarabun', 'B', 14)
                    
                    # Draw the header cell
                    pdf.cell(width, header_height, header, border=1, align='C')
                    
                    # Move to next cell position
                    current_x += width
                
                pdf.ln()
                
                # Table content with fixed row height - compact enough for 33 students
                row_height = 6.5  # Increased row height for better vertical padding
                
                for _, row in room_data.iterrows():
                    # Reset to consistent starting X position for each row
                    pdf.set_x(header_start_x)
                    
                    # Determine y position before drawing the row
                    start_y = pdf.get_y()
                    current_x = header_start_x
                    
                    # Prepare cell values
                    cell_values = [
                        str(row['เลขที่นั่งสอบ']),
                        str(row['เลขประจำตัวสอบ']),
                        str(row['ชื่อ - นามสกุล']),
                        str(row['โรงเรียน']),
                        "",  # Empty signature column
                        ""   # Empty note column
                    ]
                    
                    # Draw each cell in the row
                    for i, (width, value) in enumerate(zip(col_widths, cell_values)):
                        # Set position to current cell
                        pdf.set_xy(current_x, start_y)
                        
                        # Cell borders
                        pdf.cell(width, row_height, "", border=1)
                        
                        # Skip empty cells
                        if not value:
                            current_x += width
                            continue
                        
                        # Determine the optimal font size for this content
                        align = 'C' if i in [0, 1, 4, 5] else 'L'
                        padding = 1 if align == 'L' else 0
                        
                        # Set an appropriate font size that makes the text fit
                        font_size = self.get_optimal_font_size(pdf, value, width - (2 * padding))
                        pdf.set_font('thsarabun', '', font_size)
                        
                        # Add text content - precisely centered vertically with more padding
                        # Keep content_height the same but increase the overall row height
                        content_height = 3.5
                        y_position = start_y + (row_height - content_height) / 2
                        pdf.set_xy(current_x + padding, y_position)
                        pdf.cell(width - (2 * padding), content_height, value, align=align)
                        
                        # Move to next cell position
                        current_x += width
                    
                    # Move to next row - exactly at the end of this row
                    pdf.set_y(start_y + row_height)
            
            # Save the PDF
            pdf.output(output_file)
            logger.info(f"Successfully created PDF for program {program}: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating PDF for program {program}: {str(e)}")
            return False 