class ExamRoomConfig:
    # File and sheet name constants
    EXCEL_INPUT_FILE = "ApplicantNamelist.xlsx"
    EXCEL_SCHOOL_NAME_MAPPING_FILE = "schoolname.csv"
    SHEET_NAME = "Merge"
    
    # Program ID prefixes
    EXAM_ID_PREFIX = {
        "m1-special-epsmtp": "11",
        "m1-special-smte": "12",
        "m4-special-smte": "41",
        "m4-special-hsip": "42",
        "m4-special-ep-scimath": "43",
        "m4-special-ep-artmath": "44",
        "m4-special-lang-cn": "46",
        "m4-special-lang-jp": "45",
        "m4-special-lang-fr": "47",
    }
    
    # Program Thai names
    PROGRAM_THAI_NAME = {
        "m1-special-epsmtp": "โครงการจัดการเรียนการสอนตามหลักสูตรกระทรวงศึกษาธิการเป็นภาษาอังกฤษ และโครงการส่งเสริมความเป็นเลิศด้านวิทยาศาสตร์ คณิตศาสตร์ และเทคโนโลยี",
        "m1-special-smte": "โครงการห้องเรียนพิเศษวิทยาศาสตร์ คณิตศาสตร์ เทคโนโลยีและสิ่งแวดล้อม ระดับมัธยมศึกษาตอนต้น",
        "m4-special-smte": "โครงการห้องเรียนพิเศษวิทยาศาสตร์ คณิตศาสตร์ เทคโนโลยีและสิ่งแวดล้อม",
        "m4-special-hsip": "โครงการห้องเรียนพิเศษวิทยาศาสตร์สุขภาพ",
        "m4-special-ep-scimath": "โครงการจัดการเรียนการสอนตามหลักสูตรกระทรวงศึกษาธิการเป็นภาษาอังกฤษ แผนการเรียนวิทย์-คณิต",
        "m4-special-ep-artmath": "	โครงการจัดการเรียนการสอนตามหลักสูตรกระทรวงศึกษาธิการเป็นภาษาอังกฤษ แผนการเรียนศิลป์-คำนวณ",
        "m4-special-lang-cn": "โครงการห้องเรียนพิเศษภาษาต่างประเทศภาษาที่ 2 แผนการเรียนศิลป์ - ภาษาจีน",
        "m4-special-lang-jp": "โครงการห้องเรียนพิเศษภาษาต่างประเทศภาษาที่ 2 แผนการเรียนศิลป์ - ภาษาญี่ปุ่น",
        "m4-special-lang-fr": "โครงการห้องเรียนพิเศษภาษาต่างประเทศภาษาที่ 2 แผนการเรียนศิลป์ - ภาษาฝรั่งเศส",
    }
    
    # Title mapping
    TITLE_MAPPING = {
        "นาย": "นาย",
        "นาง": "นาง",
        "นางสาว": "นางสาว",
        "เด็กชาย": "ด.ช.",
        "เด็กหญิง": "ด.ญ."
    }
    
    # School prefixes to clean
    SCHOOL_PREFIXES = [
        "โรงเรียน", "รร.", "ร.ร.", "ร.ร", 
        "โรงเรีย", "โรวเรียน", "เรียน"
    ]

    ROOM_METADATA = {
        "321": { "building": "อาคาร 3", "floor": "2"},
        "322": { "building": "อาคาร 3", "floor": "2"},
        "323": { "building": "อาคาร 3", "floor": "2"},
        "331": { "building": "อาคาร 3", "floor": "3"},
        "332": { "building": "อาคาร 3", "floor": "3"},
        "333": { "building": "อาคาร 3", "floor": "3"},
        "721": { "building": "อาคาร 7", "floor": "2"},
        "722": { "building": "อาคาร 7", "floor": "2"},
        "723": { "building": "อาคาร 7", "floor": "2"},
        "724": { "building": "อาคาร 7", "floor": "2"},
        "725": { "building": "อาคาร 7", "floor": "2"},
        "726": { "building": "อาคาร 7", "floor": "2"},
        "727": { "building": "อาคาร 7", "floor": "2"},
        "728": { "building": "อาคาร 7", "floor": "2"},
        "742": { "building": "อาคาร 7", "floor": "4"},
        "743": { "building": "อาคาร 7", "floor": "4"},
        "744": { "building": "อาคาร 7", "floor": "4"},
        "745": { "building": "อาคาร 7", "floor": "4"},
        "746": { "building": "อาคาร 7", "floor": "4"},
        "747": { "building": "อาคาร 7", "floor": "4"},
        "748": { "building": "อาคาร 7", "floor": "4"},
        "ประดู่แดง 1": { "building": "อาคาร 6", "floor": "1"},
        "ประดู่แดง 2": { "building": "อาคาร 6", "floor": "1"},
        "ประดู่แดง 3": { "building": "อาคาร 6", "floor": "1"},
        "622": { "building": "อาคาร 6", "floor": "2"},
        "632": { "building": "อาคาร 6", "floor": "3"},
        "633": { "building": "อาคาร 6", "floor": "3"},
        "634": { "building": "อาคาร 6", "floor": "3"},
        "635": { "building": "อาคาร 6", "floor": "3"},
        "636": { "building": "อาคาร 6", "floor": "3"},
        "641": { "building": "อาคาร 6", "floor": "4"},
        "642": { "building": "อาคาร 6", "floor": "4"},
        "643": { "building": "อาคาร 6", "floor": "4"},
        "644": { "building": "อาคาร 6", "floor": "4"},
        "645": { "building": "อาคาร 6", "floor": "4"},
        "เกษตร": { "building": "อาคารเกษตร", "floor": "1"},
        "สะเต็ม": { "building": "อาตารสะเต็ม", "floor": "1"},
        "ชย.": { "building": "อาคารชย.", "floor": "1"},
    }
    
    # Exam room configurations
    EXAM_ROOMS = {
        "m1-special-epsmtp": [
        ("721", 30),
        ("722", 30),
        ("723", 30),
        ("724", 30),
        ("725", 30),
        ("726", 30),
        ("727", 30),
        ("728", 30),
        ("742", 30),
        ("743", 30),
        ("744", 30),
        ("745", 30),
        ("746", 30),
        ("747", 30),
        ("748", 30),
        ("ประดู่แดง 1", 30),
        ("ประดู่แดง 2", 30),
        ("ประดู่แดง 3", 30),
        ("622", 30),
        ("632", 30),
        ("633", 30),
        ("634", 30),
        ("635", 30),
        ("641", 30),
        ("642", 30),
        ("643", 30),
        ("644", 30),
        ("645", 30),
        ("636", 30)],
        "m1-special-smte": [
        ("321", 30),
        ("322", 30),
        ("323", 30),
        ("331", 30),
        ("332", 30),
        ("333", 30)],
        "m4-special-smte": [("721", 30), ("722", 30), ("723", 30), ("724", 30), ("725", 30), 
                            ("726", 30), ("727", 30), ("728", 30)],
        "m4-special-hsip": [("742", 30), ("743", 30), ("744", 30), ("745", 30), ("746", 30), ("747", 30), ("748", 30), ("622", 30)],
        "m4-special-ep-scimath": [("ประดู่แดง 1", 30), ("ประดู่แดง 2", 30), ("ประดู่แดง 3", 30), ("632", 30), ("633", 30)],
        "m4-special-ep-artmath": [("634", 32), ("635", 32), ("641", 33)],
        "m4-special-lang-cn": [("642", 32), ("643", 32), ("644", 31)],
        "m4-special-lang-jp": [("645", 32), ("เกษตร", 31)],
        "m4-special-lang-fr": [("สะเต็ม", 30), ("ชย.", 17)],
    }
    
    # Column names and mappings
    REQUIRED_COLUMNS = [
        "applicant.thaiID", "applicant.title", "applicant.firstName",
        "applicant.lastName", "education.currentSchool", "programID", "status"
    ]
    
    COLUMN_RENAME_MAPPING = {
        "applicant.thaiID": "thaiID",
        "applicant.title": "title",
        "applicant.firstName": "firstname",
        "applicant.lastName": "lastname",
        "education.currentSchool": "school",
        "programID": "program",
        "status": "status"
    }
    
    FINAL_COLUMN_RENAME = {
        "exam_room": "ห้องสอบ",
        "exam_no": "เลขที่นั่งสอบ",
        "exam_id": "เลขประจำตัวสอบ",
        "fullname": "ชื่อ - นามสกุล",
        "school": "โรงเรียน"
    }
    
    # Font file paths
    FONT_REGULAR = 'fonts/THSarabun.ttf'
    FONT_BOLD = 'fonts/THSarabun Bold.ttf'
    
    # Output file names
    DEFAULT_EXCEL_OUTPUT = "exam_room_assignments.xlsx"
    DEFAULT_CHECKPOINT_FILE = "exam_room_checkpoint.csv"
    PDF_OUTPUT_TEMPLATE = "pdf/exam_room_{}.pdf"
    
    # Academic year and other constants
    ACADEMIC_YEAR = "2568"  # Thai year for 2024
    M1_EXAM_DATE = "15 มีนาคม 2568"
    M4_EXAM_DATE = "16 มีนาคม 2568" 