import firebase_admin
from firebase_admin import firestore, credentials
from exam_room_app.utils.logger import logger

class Firebase:
    def __init__(self):
        self.cred = credentials.Certificate("admission-benjama-ac-th-firebase-adminsdk-yj7nd-76c6725e67.json")
        self.app = firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()

    def set_exam_room_data(self, exam_room_data: list):
        for data in exam_room_data:
            try:
                self.db.collection("exams").document(data["examID"]).set(data, merge=True)
                logger.info(f"Exam room data set for {data['examID']}")
            except Exception as e:
                logger.error(f"Error setting exam room data: {str(e)}")
                return False
        return True
    
    def set_new_school_data(self, new_school_data: list):
        for data in new_school_data:
            try:
                self.db.collection("forms").document(data["thaiID"]).set({
                    "education": {
                        "currentSchool": data["newSchool"]
                    }
                }, merge=True)

                logger.info(f"New school data set for {data['thaiID']}")
            except Exception as e:
                logger.error(f"Error setting new school data: {str(e)}")
                return False
        return True