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