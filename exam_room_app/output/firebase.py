import firebase_admin
from firebase_admin import firestore, credentials
from typing import List, Dict, Any, Optional
import os
from exam_room_app.utils.logger import logger

class Firebase:
    """
    Firebase client for interacting with Firestore database.
    
    This class handles connections to Firebase and provides methods
    to save and retrieve data from Firestore collections.
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Firebase connection with credentials.
        
        Args:
            credentials_path: Path to the Firebase credentials JSON file.
                             If None, will use FIREBASE_CREDENTIALS_PATH env var
                             or fall back to default path.
        
        Raises:
            ValueError: If credentials file cannot be found or is invalid
        """
        # Use provided path, environment variable, or default path
        self.credentials_path = credentials_path or os.environ.get(
            "FIREBASE_CREDENTIALS_PATH", 
            "admission-benjama-ac-th-firebase-adminsdk-yj7nd-76c6725e67.json"
        )
        
        if not os.path.exists(self.credentials_path):
            error_msg = f"Firebase credentials file not found at {self.credentials_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            self.cred = credentials.Certificate(self.credentials_path)
            self.app = firebase_admin.initialize_app(self.cred)
            self.db = firestore.client()
            logger.info("Firebase connection initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Firebase: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def _set_document(self, collection: str, document_id: str, data: Dict[str, Any], merge: bool = True) -> bool:
        """
        Set a document in Firestore with error handling.
        
        Args:
            collection: The collection name
            document_id: The document ID
            data: The data to set
            merge: Whether to merge with existing data (default: True)
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        try:
            self.db.collection(collection).document(document_id).set(data, merge=merge)
            logger.info(f"Document {document_id} set in {collection}")
            return True
        except Exception as e:
            logger.error(f"Error setting document {document_id} in {collection}: {str(e)}")
            return False

    def set_exam_room_data(self, exam_room_data: List[Dict[str, Any]]) -> bool:
        """
        Set exam room data for multiple exams.
        
        Args:
            exam_room_data: List of exam room data dictionaries
                           Each dict must contain an 'examID' key
                           
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        if not exam_room_data:
            logger.warning("No exam room data provided to upload")
            return True
            
        success = True
        for data in exam_room_data:
            if "examID" not in data:
                logger.error(f"Missing examID in exam room data: {data}")
                success = False
                continue
                
            result = self._set_document("exams", data["examID"], data)
            if not result:
                success = False
                
        return success
    
    def set_new_school_data(self, new_school_data: List[Dict[str, Any]]) -> bool:
        """
        Update student records with new school information.
        
        Args:
            new_school_data: List of dictionaries containing 'thaiID' and 'newSchool' keys
            
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        if not new_school_data:
            logger.warning("No new school data provided to upload")
            return True
            
        success = True
        for data in new_school_data:
            if "thaiID" not in data or "newSchool" not in data:
                logger.error(f"Missing required fields in school data: {data}")
                success = False
                continue
                
            formatted_data = {
                "education": {
                    "currentSchool": data["newSchool"]
                }
            }
            
            result = self._set_document("forms", data["thaiID"], formatted_data)
            if not result:
                success = False
                
        return success
        
    def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document from Firestore.
        
        Args:
            collection: The collection name
            document_id: The document ID
            
        Returns:
            Optional[Dict[str, Any]]: Document data or None if not found/error
        """
        try:
            doc_ref = self.db.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"Document {document_id} not found in {collection}")
                return None
                
            return doc.to_dict()
        except Exception as e:
            logger.error(f"Error retrieving document {document_id} from {collection}: {str(e)}")
            return None