"""
Medical Terminology Validator

Validates and corrects medical terminology in transcripts
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TerminologyCorrection:
    """Represents a terminology correction"""
    original: str
    corrected: str
    confidence: float
    correction_type: str  # "spelling", "normalization", "expansion"


class MedicalTerminologyValidator:
    """
    Validates and corrects medical terminology
    
    Features:
    - Medical term spelling correction
    - Abbreviation expansion
    - Terminology normalization
    - Common medical term variations
    """
    
    def __init__(self):
        """Initialize medical terminology validator"""
        self.medical_abbreviations = self._build_abbreviation_dict()
        self.medical_corrections = self._build_correction_dict()
        self.common_variations = self._build_variation_dict()
        self.common_words_whitelist = self._build_common_words_whitelist()
        logger.info("Medical terminology validator initialized")
    
    def _build_common_words_whitelist(self) -> set:
        """Build whitelist of common English words that should never be corrected"""
        return {
            # Common articles, prepositions, conjunctions
            "a", "an", "the", "and", "or", "but", "for", "of", "to", "in", "on", "at",
            "by", "with", "from", "as", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "this", "that", "these", "those",
            # Numbers (as strings)
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "20", "30",
            "40", "50", "60", "70", "80", "90", "100", "120", "140", "150",
            # Common medical context words
            "patient", "doctor", "nurse", "hospital", "clinic", "report", "reports",
            "diagnosis", "diagnosed", "prescribed", "prescription", "medication",
            "treatment", "examination", "test", "result", "results", "condition",
            # Units and measurements
            "c", "f", "mg", "ml", "l", "kg", "g", "mm", "cm", "m", "in", "ft",
            "bpm", "mmHg", "mmhg", "degrees", "degree"
        }
    
    def _build_abbreviation_dict(self) -> Dict[str, str]:
        """Build dictionary of medical abbreviations and expansions"""
        return {
            "bp": "blood pressure",
            "hr": "heart rate",
            "rr": "respiratory rate",
            "temp": "temperature",
            "spo2": "oxygen saturation",
            "bpm": "beats per minute",
            "cbc": "complete blood count",
            "ekg": "electrocardiogram",
            "ecg": "electrocardiogram",
            "mri": "magnetic resonance imaging",
            "ct": "computed tomography",
            "copd": "chronic obstructive pulmonary disease",
            "mi": "myocardial infarction",
            "chf": "congestive heart failure",
            "uti": "urinary tract infection",
            "pneumonia": "pneumonia",
            "diabetes": "diabetes mellitus",
            "htn": "hypertension",
            "dm": "diabetes mellitus",
        }
    
    def _build_correction_dict(self) -> Dict[str, str]:
        """Build dictionary of common misspellings and corrections"""
        return {
            # Common misspellings
            "fever": ["fever", "feverish", "fevered"],
            "cough": ["cough", "coughing"],
            "pain": ["pain", "painful", "pains"],
            "headache": ["headache", "head ache", "head-ache"],
            "nausea": ["nausea", "nauseous", "nauseated"],
            "vomiting": ["vomiting", "vomit", "vomited"],
            "dizziness": ["dizziness", "dizzy", "dizzyness"],
            "fatigue": ["fatigue", "fatigued", "tiredness"],
            "pneumonia": ["pneumonia", "pneumoniae", "pneumonitis"],
            "bronchitis": ["bronchitis", "bronchititis"],
            "diabetes": ["diabetes", "diabetis", "diabetus"],
            "hypertension": ["hypertension", "hypertention", "hypertenssion"],
            "medication": ["medication", "medication", "medicaton"],
            "prescription": ["prescription", "presciption", "prescrition"],
        }
    
    def _build_variation_dict(self) -> Dict[str, List[str]]:
        """Build dictionary of common medical term variations"""
        return {
            "blood pressure": ["bp", "blood pressure", "bloodpressure"],
            "heart rate": ["hr", "heart rate", "pulse", "pulse rate"],
            "temperature": ["temp", "temperature", "fever"],
            "shortness of breath": ["sob", "shortness of breath", "dyspnea", "dyspnoea"],
            "chest pain": ["chest pain", "chest discomfort", "chest pressure"],
            "abdominal pain": ["abdominal pain", "stomach pain", "belly pain"],
        }
    
    def validate_term(self, term: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a medical term
        
        Args:
            term: Term to validate
            
        Returns:
            Tuple of (is_valid, corrected_term)
        """
        term_lower = term.lower().strip()
        
        # Check if it's a known abbreviation
        if term_lower in self.medical_abbreviations:
            return True, self.medical_abbreviations[term_lower]
        
        # Check if it's a known term (exact match)
        all_terms = set()
        all_terms.update(self.medical_abbreviations.keys())
        all_terms.update(self.medical_abbreviations.values())
        for variations in self.common_variations.values():
            all_terms.update(variations)
        
        if term_lower in all_terms:
            return True, term_lower
        
        # Check for common variations
        for standard, variations in self.common_variations.items():
            if term_lower in variations:
                return True, standard
        
        # Check for corrections
        for correct, misspellings in self.medical_corrections.items():
            if term_lower in misspellings:
                return True, correct
        
        # Try fuzzy matching (simple edit distance) - but only for medical terms, not numbers
        if not term_lower.isdigit() and len(term_lower) >= 3:  # Only fuzzy match words 3+ chars, not numbers
            corrected = self._fuzzy_match(term_lower, all_terms)
            if corrected:
                return True, corrected
        
        return False, None
    
    def _fuzzy_match(self, term: str, dictionary: set, max_distance: int = 2) -> Optional[str]:
        """
        Simple fuzzy matching using edit distance
        
        Args:
            term: Term to match
            dictionary: Set of valid terms
            max_distance: Maximum edit distance
            
        Returns:
            Closest match or None
        """
        # Simple Levenshtein-like distance
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
        
        for dict_term in dictionary:
            distance = edit_distance(term, dict_term)
            if distance < best_distance:
                best_distance = distance
                best_match = dict_term
        
        return best_match if best_match else None
    
    def correct_text(self, text: str) -> Tuple[str, List[TerminologyCorrection]]:
        """
        Correct medical terminology in text
        
        Args:
            text: Text to correct
            
        Returns:
            Tuple of (corrected_text, list_of_corrections)
        """
        corrections = []
        corrected_text = text
        
        # Split text into words
        words = re.findall(r'\b\w+\b', text)
        word_positions = []
        current_pos = 0
        for word in words:
            pos = text.find(word, current_pos)
            word_positions.append((word, pos, pos + len(word)))
            current_pos = pos + len(word)
        
        # Check each word
        for word, start_pos, end_pos in word_positions:
            word_lower = word.lower()
            
            # Skip common English words - never correct these
            if word_lower in self.common_words_whitelist:
                continue
            
            # Skip pure numbers - never correct these
            if word_lower.isdigit():
                continue
            
            is_valid, corrected = self.validate_term(word)
            if not is_valid or (corrected and corrected != word_lower):
                if corrected:
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
                    
                    corrections.append(TerminologyCorrection(
                        original=word,
                        corrected=corrected,
                        confidence=0.8,
                        correction_type="spelling" if not is_valid else "normalization"
                    ))
        
        # Expand abbreviations (only in medical contexts)
        for abbrev, expansion in self.medical_abbreviations.items():
            # Only expand if abbreviation is 2+ characters (avoid single letters like "C")
            if len(abbrev) < 2:
                continue
            
            # Use word boundary to avoid matching parts of words
            pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b', re.IGNORECASE)
            matches = list(pattern.finditer(corrected_text))
            
            for match in matches:
                # Check context - only expand if in medical context
                start, end = match.span()
                context_start = max(0, start - 20)
                context_end = min(len(corrected_text), end + 20)
                context = corrected_text[context_start:context_end].lower()
                
                # Medical context indicators
                medical_indicators = [
                    "patient", "doctor", "diagnosis", "symptom", "treatment",
                    "medication", "prescription", "blood", "heart", "pressure",
                    "rate", "temperature", "test", "result", "examination"
                ]
                
                # Only expand if in medical context
                if any(indicator in context for indicator in medical_indicators):
                    # Check if expansion is already present nearby
                    if expansion.lower() not in context:
                        corrected_text = corrected_text[:start] + expansion + corrected_text[end:]
                        corrections.append(TerminologyCorrection(
                            original=abbrev,
                            corrected=expansion,
                            confidence=0.9,
                            correction_type="expansion"
                        ))
                        break  # Only expand first occurrence per abbreviation
        
        return corrected_text, corrections
    
    def get_terminology_summary(self, text: str) -> Dict[str, Any]:
        """
        Get summary of medical terminology in text
        
        Args:
            text: Text to analyze
            
        Returns:
            Summary dictionary
        """
        words = re.findall(r'\b\w+\b', text)
        medical_terms = []
        abbreviations = []
        corrections = []
        
        for word in words:
            is_valid, corrected = self.validate_term(word)
            if is_valid:
                if word.lower() in self.medical_abbreviations:
                    abbreviations.append(word)
                medical_terms.append(corrected or word)
            elif corrected:
                corrections.append({
                    "original": word,
                    "corrected": corrected
                })
        
        return {
            "total_words": len(words),
            "medical_terms": list(set(medical_terms)),
            "abbreviations": list(set(abbreviations)),
            "corrections": corrections,
            "medical_term_ratio": len(medical_terms) / len(words) if words else 0
        }

