"""
Medical Spell Checker

Spell-checking specifically for medical terminology
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpellCorrection:
    """Represents a spell correction"""
    original: str
    corrected: str
    confidence: float
    suggestions: List[str]


class MedicalSpellChecker:
    """
    Medical terminology spell checker
    
    Features:
    - Medical term dictionary
    - Common medical misspellings
    - Context-aware corrections
    - Confidence scoring
    """
    
    def __init__(self):
        """Initialize medical spell checker"""
        self.medical_dictionary = self._build_medical_dictionary()
        self.common_misspellings = self._build_misspelling_dict()
        self.common_words_whitelist = self._build_common_words_whitelist()
        logger.info("Medical spell checker initialized")
    
    def _build_common_words_whitelist(self) -> set:
        """Build whitelist of common English words that should never be corrected"""
        return {
            # Common articles, prepositions, conjunctions
            "a", "an", "the", "and", "or", "but", "for", "of", "to", "in", "on", "at",
            "by", "with", "from", "as", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these", "those",
            "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
            "my", "your", "his", "her", "its", "our", "their", "what", "which",
            "who", "when", "where", "why", "how", "all", "some", "any", "no",
            "not", "if", "then", "else", "so", "than", "more", "most", "less",
            "very", "too", "also", "just", "only", "even", "still", "yet", "now",
            "then", "here", "there", "where", "when", "why", "how", "what",
            # Common verbs
            "get", "got", "go", "went", "come", "came", "see", "saw", "know",
            "think", "thought", "say", "said", "tell", "told", "ask", "asked",
            "give", "gave", "take", "took", "make", "made", "find", "found",
            "work", "worked", "try", "tried", "use", "used", "want", "wanted",
            "need", "needed", "feel", "felt", "seem", "seemed", "look", "looked",
            "call", "called", "show", "showed", "let", "let", "help", "helped",
            # Numbers and common words
            "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
            "first", "second", "third", "last", "next", "new", "old", "good", "bad",
            "big", "small", "long", "short", "high", "low", "right", "left",
            "up", "down", "out", "off", "over", "under", "again", "further",
            # Medical context words that are common English
            "patient", "doctor", "nurse", "hospital", "clinic", "report", "reports",
            "diagnosis", "diagnosed", "prescribed", "prescription", "medication",
            "treatment", "examination", "test", "result", "results", "condition",
            "disease", "illness", "symptom", "symptoms", "sign", "signs"
        }
    
    def _build_medical_dictionary(self) -> set:
        """Build medical terminology dictionary"""
        medical_terms = {
            # Symptoms
            "fever", "cough", "pain", "headache", "nausea", "vomiting",
            "dizziness", "fatigue", "shortness", "breath", "chest", "abdominal",
            "rash", "itching", "swelling", "bleeding", "diarrhea", "constipation",
            
            # Diagnoses
            "pneumonia", "bronchitis", "asthma", "diabetes", "hypertension",
            "infection", "bacterial", "viral", "flu", "influenza", "cold",
            "sinusitis", "pharyngitis", "tonsillitis", "gastritis", "ulcer",
            "arthritis", "osteoporosis", "anemia",
            
            # Medications
            "aspirin", "ibuprofen", "paracetamol", "acetaminophen",
            "antibiotic", "penicillin", "amoxicillin", "antihistamine",
            "steroid", "prednisone", "insulin", "metformin", "antacid",
            "painkiller", "analgesic", "antipyretic",
            
            # Vital signs
            "blood", "pressure", "heart", "rate", "pulse", "temperature",
            "respiratory", "oxygen", "saturation",
            
            # Procedures
            "surgery", "operation", "biopsy", "endoscopy", "colonoscopy",
            "ultrasound", "electrocardiogram",
            
            # Body parts
            "chest", "abdomen", "head", "neck", "arm", "leg", "back",
            "shoulder", "knee", "elbow", "wrist", "ankle", "foot", "hand",
            "heart", "lung", "liver", "kidney", "stomach", "intestine",
            "brain", "spine", "bone", "muscle", "joint",
            
            # Medical terms
            "patient", "doctor", "physician", "nurse", "hospital", "clinic",
            "diagnosis", "symptom", "treatment", "medication", "prescription",
            "examination", "test", "result", "condition", "disease", "illness",
        }
        return medical_terms
    
    def _build_misspelling_dict(self) -> Dict[str, str]:
        """Build dictionary of common medical misspellings"""
        return {
            "fever": ["fever", "feverish"],
            "cough": ["cough", "coughing"],
            "pneumonia": ["pneumonia", "pneumoniae", "pneumonitis"],
            "bronchitis": ["bronchitis", "bronchititis"],
            "diabetes": ["diabetes", "diabetis", "diabetus"],
            "hypertension": ["hypertension", "hypertention", "hypertenssion"],
            "medication": ["medication", "medicaton", "medicatin"],
            "prescription": ["prescription", "presciption", "prescrition"],
            "nausea": ["nausea", "nausia", "nausa"],
            "dizziness": ["dizziness", "dizzyness", "diziness"],
            "fatigue": ["fatigue", "fatige", "fatige"],
        }
    
    def check_spelling(self, word: str) -> Tuple[bool, Optional[str], float]:
        """
        Check spelling of a word
        
        Args:
            word: Word to check
            
        Returns:
            Tuple of (is_correct, corrected_word, confidence)
        """
        word_lower = word.lower().strip()
        
        # Check if word is in dictionary
        if word_lower in self.medical_dictionary:
            return True, None, 1.0
        
        # Check common misspellings
        for correct, variations in self.common_misspellings.items():
            if word_lower in variations:
                return False, correct, 0.9
        
        # Try fuzzy matching
        corrected = self._fuzzy_match(word_lower, self.medical_dictionary)
        if corrected:
            return False, corrected, 0.7
        
        return False, None, 0.0
    
    def _fuzzy_match(self, word: str, dictionary: set, max_distance: int = 2) -> Optional[str]:
        """
        Fuzzy match word against dictionary
        
        Args:
            word: Word to match
            dictionary: Set of valid words
            max_distance: Maximum edit distance
            
        Returns:
            Closest match or None
        """
        def edit_distance(s1: str, s2: str) -> int:
            if len(s1) < len(s2):
                return edit_distance(s2, s1)
            if len(s2) == 0:
                return len(s1)
            
            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            return previous_row[-1]
        
        best_match = None
        best_distance = max_distance + 1
        
        for dict_word in dictionary:
            distance = edit_distance(word, dict_word)
            if distance < best_distance:
                best_distance = distance
                best_match = dict_word
        
        return best_match if best_match else None
    
    def correct_text(self, text: str) -> Tuple[str, List[SpellCorrection]]:
        """
        Correct spelling in text
        
        Args:
            text: Text to correct
            
        Returns:
            Tuple of (corrected_text, list_of_corrections)
        """
        corrections = []
        corrected_text = text
        
        # Find all words
        words = re.findall(r'\b\w+\b', text)
        word_positions = []
        current_pos = 0
        for word in words:
            pos = text.find(word, current_pos)
            word_positions.append((word, pos, pos + len(word)))
            current_pos = pos + len(word)
        
        # Check and correct each word
        for word, start_pos, end_pos in word_positions:
            word_lower = word.lower()
            
            # Skip common English words - never correct these
            if word_lower in self.common_words_whitelist:
                continue
            
            is_correct, corrected, confidence = self.check_spelling(word)
            if not is_correct and corrected and confidence >= 0.8:  # Only correct with high confidence
                # Replace word in text
                original_word = text[start_pos:end_pos]
                # Preserve case
                if word.isupper():
                    replacement = corrected.upper()
                elif word[0].isupper():
                    replacement = corrected.capitalize()
                else:
                    replacement = corrected
                
                corrected_text = corrected_text.replace(original_word, replacement, 1)
                
                corrections.append(SpellCorrection(
                    original=word,
                    corrected=corrected,
                    confidence=confidence,
                    suggestions=[corrected]
                ))
        
        return corrected_text, corrections
    
    def get_suggestions(self, word: str, max_suggestions: int = 5) -> List[str]:
        """
        Get spelling suggestions for a word
        
        Args:
            word: Word to get suggestions for
            max_suggestions: Maximum number of suggestions
            
        Returns:
            List of suggested corrections
        """
        suggestions = []
        word_lower = word.lower()
        
        # Check common misspellings
        for correct, variations in self.common_misspellings.items():
            if word_lower in variations:
                suggestions.append(correct)
        
        # Fuzzy match
        corrected = self._fuzzy_match(word_lower, self.medical_dictionary)
        if corrected and corrected not in suggestions:
            suggestions.append(corrected)
        
        return suggestions[:max_suggestions]

