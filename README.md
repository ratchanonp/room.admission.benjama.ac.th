# Exam Room Assignment Generator

A Python application for generating exam room assignments for student applicants.

## Features

- Load student applicant data from Excel files
- Clean and process student data
- Assign exam rooms and seat numbers based on program requirements
- Generate Excel output with exam assignments
- Create PDF files with formatted room assignment lists

## Requirements

- Python 3.7+
- Required packages: pandas, numpy, openpyxl, fpdf

## Installation

1. Clone this repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the application with default settings:

```bash
python -m exam_room_app
```

Or specify custom parameters:

```bash
python -m exam_room_app --input-file "path/to/input.xlsx" --sheet-name "SheetName" --output-excel "output.xlsx"
```

### Command Line Arguments

- `--input-file`: Path to the input Excel file (default: "ApplicantNamelist.xlsx")
- `--sheet-name`: Name of the sheet to process (default: "Merge")
- `--output-excel`: Path to the output Excel file (default: "exam_room_assignments.xlsx")

## Project Structure

- `exam_room_app/`: Main package
  - `config/`: Configuration and constants
  - `data_processing/`: Data loading and processing modules
  - `output/`: Output generation (Excel, PDF)
  - `utils/`: Utility functions and logging
  - `app.py`: Main application class
  - `__main__.py`: Entry point

## Expected Input Format

The input Excel file should contain the following columns:
- applicant.thaiID
- applicant.title
- applicant.firstName
- applicant.lastName
- education.currentSchool
- programID
- status

## Output

The application generates:
1. An Excel file with separate sheets for each program
2. PDF files for each program with detailed room assignments

## License

MIT 