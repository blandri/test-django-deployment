from PIL import Image, ImageEnhance, ImageFilter
import torch
from transformers import CLIPProcessor, CLIPModel
import numpy as np
import os
from typing import List, Optional, Dict, Any, Tuple
import logging
from pathlib import Path
import cv2
import re
from collections import defaultdict
import easyocr

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.model_name = "openai/clip-vit-base-patch32"
        self.processor = None
        self.reader = easyocr.Reader(['en'])
        self.model = None
        self.load_model()
        
        # Workflow-specific keywords and patterns
        self.workflow_keywords = {
            'actions': ['apply', 'login', 'payment', 'approve', 'decline', 'submit', 'confirm', 'receive', 'send'],
            'actors': ['applicant', 'officer', 'user', 'system', 'admin', 'citizen', 'irembogov engine'],
            'decision_words': ['successful', 'approved', 'declined', 'yes', 'no', 'decision'],
            'notification_words': ['notification', 'email', 'sms', 'message', 'alert'],
            'process_words': ['start', 'end', 'stop', 'begin', 'finish', 'process']
        }
    
    def load_model(self):
        """Load CLIP model for image embeddings"""
        try:
            self.processor = CLIPProcessor.from_pretrained(self.model_name)
            self.model = CLIPModel.from_pretrained(self.model_name)
            logger.info("CLIP model loaded successfully for image processing")
        except Exception as e:
            logger.error(f"Error loading CLIP model: {e}")

    def extract_workflow_info_from_image(self, image_path: Path) -> Dict[str, Any]:
        """Extract comprehensive workflow information from diagram images"""
        try:
            image = Image.open(image_path)
            
            # Extract text using OCR
            extracted_text = self._extract_text_with_ocr(image)

            # Analyze workflow structure
            workflow_analysis = self._analyze_workflow_structure(extracted_text)
            
            # Detect workflow elements
            workflow_elements = self._detect_workflow_elements(extracted_text)
            
            # Extract actors and roles
            actors_and_roles = self._extract_actors_and_roles(extracted_text)
            
            # Identify process steps
            process_steps = self._identify_process_steps(extracted_text)
            
            # Detect decision points
            decision_points = self._detect_decision_points(extracted_text)
            
            # Extract notifications
            notifications = self._extract_notifications_from_image(extracted_text)
            
            comprehensive_info = {
                'image_type': "Work flow diagram",
                'extracted_text': extracted_text,
                'workflow_analysis': workflow_analysis,
                'workflow_elements': workflow_elements,
                'actors_and_roles': actors_and_roles,
                'process_steps': process_steps,
                'decision_points': decision_points,
                'notifications': notifications
                # 'test_scenarios': self._generate_test_scenarios_from_workflow(workflow_elements, process_steps, decision_points)
            }
            
            return comprehensive_info
        except Exception as e:
            logger.error(f"Error extracting workflow info from image {image_path}: {e}")
            raise
    
    def generate_image_embedding(self, image_path: Path) -> Optional[List[float]]:
        """Generate embedding for an image with enhanced preprocessing"""
        try:
            if not self.model or not self.processor:
                logger.error("CLIP model not loaded")
                return None
            
            # Load and enhance image
            image = Image.open(image_path).convert('RGB')
            
            # Enhance image for better processing
            enhanced_image = self._enhance_image_for_ocr(image)
            
            # Process image with CLIP
            inputs = self.processor(images=enhanced_image, return_tensors="pt")
            
            # Generate embedding
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                # Normalize the features
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.squeeze().tolist()
        except Exception as e:
            logger.error(f"Error generating image embedding for {image_path}: {e}")
            return None
    
    def generate_text_image_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using CLIP (for text-image similarity)"""
        try:
            if not self.model or not self.processor:
                logger.error("CLIP model not loaded")
                return None
            
            # Process text
            inputs = self.processor(text=[text], return_tensors="pt", padding=True)
            
            # Generate embedding
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
                # Normalize the features
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            return text_features.squeeze().tolist()
        except Exception as e:
            logger.error(f"Error generating text-image embedding: {e}")
            return None
    
    
    def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results"""
        try:
            # Convert to grayscale for better OCR
            if image.mode != 'L':
                image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            
            # Apply slight gaussian blur to smooth out noise
            image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Convert back to RGB for CLIP
            return image.convert('RGB')
        except Exception as e:
            logger.error(f"Error enhancing image: {e}")
            return image
    
    def _extract_text_with_ocr(self, image: Image.Image) -> str:
        try:
            image_array = np.array(image.convert('RGB'))
            
            # Apply preprocessing for better OCR results
            processed_image = self._preprocess_image_for_easy_ocr(image_array)
           
            ocr_results = self.reader.readtext(processed_image)
            
            # Extract text from results with confidence filtering
            extracted_texts = []
            for result in ocr_results:
                if len(result) >= 3:
                    bbox, text, confidence = result
                    # Only include text with reasonable confidence (>0.5)
                    if confidence > 0.5 and text.strip():
                        extracted_texts.append(text.strip())
            
            # Join all extracted text
            full_text = ' '.join(extracted_texts)
            
            # Clean and normalize the text
            cleaned_text = self._clean_extracted_text(full_text)
            
            logger.info(f"EasyOCR extracted {len(extracted_texts)} text segments with confidence > 0.5")
            return cleaned_text

        except Exception as e:
            logger.error(f"Error extracting text with OCR: {e}")
            return ""
        
    def _preprocess_image_for_easy_ocr(self, image_array: np.ndarray) -> np.ndarray:
        """Preprocess image specifically for EasyOCR"""
        try:
            # Validate input
            if image_array is None or image_array.size == 0:
                raise ValueError("Invalid image array")
            
            # EasyOCR handles preprocessing internally, so we do minimal processing
            
            # Ensure RGB format (EasyOCR expects RGB)
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                # Already RGB, just ensure proper data type
                processed = image_array.astype(np.uint8)
            else:
                # Convert grayscale to RGB if needed
                if len(image_array.shape) == 2:
                    processed = cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
                else:
                    processed = image_array.astype(np.uint8)
            
            # Optional: Apply slight contrast enhancement
            try:
                # Convert to LAB color space for better contrast enhancement
                lab = cv2.cvtColor(processed, cv2.COLOR_RGB2LAB)
                l, a, b = cv2.split(lab)
                
                # Apply CLAHE to L channel
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
                l = clahe.apply(l)
                
                # Merge channels and convert back to RGB
                enhanced = cv2.merge([l, a, b])
                processed = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)
            except Exception as e:
                logger.warning(f"Contrast enhancement failed: {e}, using original")
                # Keep original processed image
            
            return processed
            
        except Exception as e:
            logger.error(f"Error preprocessing image for EasyOCR: {e}")
            # Return original image if preprocessing fails
            if len(image_array.shape) == 2:
                return cv2.cvtColor(image_array, cv2.COLOR_GRAY2RGB)
            return image_array.astype(np.uint8)
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and normalize OCR extracted text"""
        try:
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove special characters that are likely OCR errors
            text = re.sub(r'[^\w\s\.\,\?\!$$$$\[\]\-]', '', text)
            
            # Fix common OCR mistakes
            text = text.replace('0', 'O').replace('1', 'I').replace('5', 'S')
            
            # Remove very short fragments (likely OCR noise)
            words = text.split()
            words = [word for word in words if len(word) > 1 or word.lower() in ['i', 'a']]
            
            return ' '.join(words).strip()
        except Exception as e:
            logger.error(f"Error cleaning extracted text: {e}")
            return text
    
    def _analyze_workflow_structure(self, text: str) -> Dict[str, Any]:
        """Analyze the overall structure of the workflow"""
        try:
            text_lower = text.lower()
            
            analysis = {
                'has_swimlanes': any(keyword in text_lower for keyword in ['applicant', 'officer', 'system', 'engine']),
                'has_decision_points': any(keyword in text_lower for keyword in ['yes', 'no', 'successful', 'approved', 'declined']),
                'has_notifications': any(keyword in text_lower for keyword in ['notification', 'email', 'sms', 'message']),
                'has_payment_flow': any(keyword in text_lower for keyword in ['payment', 'bill id']),
                'has_approval_process': any(keyword in text_lower for keyword in ['approve', 'approval', 'confirm'])
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing workflow structure: {e}")
            return {}
    
    def _detect_workflow_elements(self, text: str) -> Dict[str, List[str]]:
        """Detect different types of workflow elements"""
        try:
            text_lower = text.lower()
            elements = defaultdict(list)
            
            # Detect actions/processes
            for keyword in self.workflow_keywords['actions']:
                if keyword in text_lower:
                    # Extract context around the keyword
                    context = self._extract_context_around_keyword(text, keyword)
                    if context:
                        elements['actions'].append(context)
            
            # Detect actors/roles
            for keyword in self.workflow_keywords['actors']:
                if keyword in text_lower:
                    context = self._extract_context_around_keyword(text, keyword)
                    if context:
                        elements['actors'].append(context)
            
            # Detect decisions
            for keyword in self.workflow_keywords['decision_words']:
                if keyword in text_lower:
                    context = self._extract_context_around_keyword(text, keyword)
                    if context:
                        elements['decisions'].append(context)
            
            return dict(elements)
        except Exception as e:
            logger.error(f"Error detecting workflow elements: {e}")
            return {}
    
    def _extract_context_around_keyword(self, text: str, keyword: str, context_window: int = 10) -> str:
        """Extract context around a keyword"""
        try:
            words = text.split()
            keyword_indices = [i for i, word in enumerate(words) if keyword.lower() in word.lower()]
            
            contexts = []
            for idx in keyword_indices:
                start = max(0, idx - context_window)
                end = min(len(words), idx + context_window + 1)
                context = ' '.join(words[start:end])
                contexts.append(context)
            
            return ' | '.join(contexts) if contexts else ""
        except Exception as e:
            logger.error(f"Error extracting context around keyword {keyword}: {e}")
            return ""
    
    def _extract_actors_and_roles(self, text: str) -> List[Dict[str, str]]:
        """Extract actors and their roles from the workflow"""
        try:
            actors = []
            text_lower = text.lower()
            
            # Common actor patterns in workflows
            actor_patterns = [
                (r'district\s+applicant', 'District Applicant'),
                (r'rab\s+officer', 'RAB Officer'),
                (r'applicant', 'Applicant'),
                (r'officer', 'Officer'),
                (r'user', 'User'),
                (r'citizen', 'Citizen'),
                (r'system', 'System'),
                (r'engine', 'System Engine')
            ]
            
            for pattern, role_name in actor_patterns:
                if re.search(pattern, text_lower):
                    actors.append({
                        'name': role_name,
                        'type': 'human' if role_name not in ['System', 'System Engine'] else 'system',
                        'context': self._extract_context_around_keyword(text, role_name.split()[0])
                    })
            
            return actors
        except Exception as e:
            logger.error(f"Error extracting actors and roles: {e}")
            return []
    
    def _identify_process_steps(self, text: str) -> List[Dict[str, str]]:
        """Identify individual process steps"""
        try:
            steps = []
            
            # Look for action words that indicate process steps
            action_patterns = [
                r'login\s+to\s+(?:the\s+)?portal',
                r'apply\s+for\s+[\w\s]+',
                r'make\s+payment',
                r'receive\s+notification',
                r'confirm\s+[\w\s]+',
                r'approve\s+[\w\s]*',
                r'decline\s+[\w\s]*',
                r'send\s+notification'
            ]
            
            for i, pattern in enumerate(action_patterns):
                matches = re.findall(pattern, text.lower())
                for match in matches:
                    steps.append({
                        'step_number': str(i + 1),
                        'action': match.title(),
                        'type': 'user_action' if any(word in match for word in ['login', 'apply', 'make']) else 'system_action'
                    })
            
            return steps
        except Exception as e:
            logger.error(f"Error identifying process steps: {e}")
            return []
    
    def _detect_decision_points(self, text: str) -> List[Dict[str, str]]:
        """Detect decision points in the workflow"""
        try:
            decisions = []
            text_lower = text.lower()
            
            # Decision patterns
            decision_patterns = [
                r'is\s+payment\s+successful',
                r'approved\s+or\s+decline',
                r'yes\s+or\s+no',
                r'successful\s+\?'
            ]
            
            for pattern in decision_patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    decisions.append({
                        'decision_text': match.title(),
                        'type': 'binary_decision',
                        'possible_outcomes': self._extract_decision_outcomes(text, match)
                    })
            
            return decisions
        except Exception as e:
            logger.error(f"Error detecting decision points: {e}")
            return []
    
    def _extract_decision_outcomes(self, text: str, decision_text: str) -> List[str]:
        """Extract possible outcomes for a decision"""
        try:
            # Look for yes/no, approve/decline, etc.
            outcomes = []
            text_lower = text.lower()
            
            common_outcomes = [
                ['yes', 'no'],
                ['approved', 'declined'],
                ['successful', 'failed'],
                ['accept', 'reject']
            ]
            
            for outcome_pair in common_outcomes:
                if all(outcome in text_lower for outcome in outcome_pair):
                    outcomes.extend(outcome_pair)
                    break
            
            return list(set(outcomes))
        except Exception as e:
            logger.error(f"Error extracting decision outcomes: {e}")
            return []
    
    def _extract_notifications_from_image(self, text: str) -> List[Dict[str, str]]:
        """Extract notification-related information"""
        try:
            notifications = []
            text_lower = text.lower()
            
            # Notification patterns
            notification_patterns = [
                r'user\s+receives\s+email\s+notification',
                r'notification\s+is\s+sent',
                r'email\s+notification\s+for\s+[\w\s]+',
                r'sms\s+notification'
            ]
            
            for pattern in notification_patterns:
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    notifications.append({
                        'type': 'email' if 'email' in match else 'sms' if 'sms' in match else 'general',
                        'description': match.title(),
                        'trigger': self._extract_notification_trigger(text, match)
                    })
            
            return notifications
        except Exception as e:
            logger.error(f"Error extracting notifications: {e}")
            return []
    
    def _extract_notification_trigger(self, text: str, notification_text: str) -> str:
        """Extract what triggers a notification"""
        try:
            # Look for context before the notification
            words = text.lower().split()
            notification_words = notification_text.split()
            
            for i, word in enumerate(words):
                if notification_words[0] in word:
                    # Look at previous context
                    start = max(0, i - 5)
                    trigger_context = ' '.join(words[start:i])
                    return trigger_context.title()
            
            return "Unknown trigger"
        except Exception as e:
            logger.error(f"Error extracting notification trigger: {e}")
            return "Unknown trigger"
    
    def _generate_test_scenarios_from_workflow(self, elements: Dict, steps: List, decisions: List) -> List[Dict[str, str]]:
        """Generate potential test scenarios based on workflow analysis"""
        try:
            scenarios = []
            
            # Generate scenarios for each action
            for action in elements.get('actions', []):
                scenarios.append({
                    'type': 'functional_test',
                    'scenario': f"Test {action} functionality",
                    'priority': 'P1',
                    'category': 'user_action'
                })
            
            # Generate scenarios for decision points
            for decision in decisions:
                for outcome in decision.get('possible_outcomes', []):
                    scenarios.append({
                        'type': 'decision_test',
                        'scenario': f"Test {decision['decision_text']} with {outcome} outcome",
                        'priority': 'P1',
                        'category': 'business_logic'
                    })
            
            # Generate scenarios for each actor
            for actor in elements.get('actors', []):
                scenarios.append({
                    'type': 'role_based_test',
                    'scenario': f"Test workflow from {actor} perspective",
                    'priority': 'P2',
                    'category': 'user_role'
                })
            
            return scenarios
        except Exception as e:
            logger.error(f"Error generating test scenarios: {e}")
            return []
    
    def get_image_analysis_summary(self, image_path: Path) -> str:
        """Get a comprehensive summary of the image analysis for embedding"""
        try:
            info = self.extract_workflow_info_from_image(image_path)
            
            summary_parts = []
            
            # Add basic info
            summary_parts.append(f"Image Type: {info.get('image_type', 'unknown')}")
            
            # Add extracted text summary
            if info.get('extracted_text'):
                summary_parts.append(f"Content: {info['extracted_text'][:200]}...")
            
            # Add workflow analysis
            workflow_analysis = info.get('workflow_analysis', {})
            if workflow_analysis.get('has_swimlanes'):
                summary_parts.append("Contains swimlane diagram with multiple actors")
            if workflow_analysis.get('has_decision_points'):
                summary_parts.append("Contains decision points and branching logic")
            if workflow_analysis.get('has_notifications'):
                summary_parts.append("Contains notification workflows")
            
            # Add actors
            actors = info.get('actors_and_roles', [])
            if actors:
                actor_names = [actor['name'] for actor in actors]
                summary_parts.append(f"Actors: {', '.join(actor_names)}")
            
            # Add process steps
            steps = info.get('process_steps', [])
            if steps:
                step_actions = [step['action'] for step in steps[:3]]
                summary_parts.append(f"Key Actions: {', '.join(step_actions)}")
            
            return " | ".join(summary_parts)
        except Exception as e:
            logger.error(f"Error creating image analysis summary: {e}")
            return f"Image analysis error: {str(e)}"