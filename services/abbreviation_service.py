"""
Abbreviation expansion service using Gemini AI
"""
import json
import time
import logging
from typing import Dict, Set
import google.generativeai as genai
from config import settings
from core.exceptions import AbbreviationExpansionError

logger = logging.getLogger(__name__)


class AbbreviationService:
    """Service for expanding company name abbreviations using Gemini AI"""
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel("models/gemini-2.0-flash-lite")
        self.abbreviation_map = {}
        self.load_existing_abbreviations()
    
    def load_existing_abbreviations(self):
        """Load existing abbreviations from file if available"""
        try:
            with open('abbreviations.json', 'r') as f:
                self.abbreviation_map = json.load(f)
                logger.info(f"Loaded {len(self.abbreviation_map)} existing abbreviations")
        except FileNotFoundError:
            logger.info("No existing abbreviations file found, starting fresh")
        except Exception as e:
            logger.error(f"Error loading abbreviations: {e}")
    
    def save_abbreviations(self):
        """Save abbreviations to file"""
        try:
            with open('abbreviations.json', 'w') as f:
                json.dump(self.abbreviation_map, f, indent=2, ensure_ascii=False)
            
            # Create backup
            import shutil
            shutil.copy('abbreviations.json', 'abbreviations_backup.json')
            logger.info("Abbreviations saved successfully")
        except Exception as e:
            logger.error(f"Error saving abbreviations: {e}")
    
    def extract_abbreviations(self, company_names: list) -> Set[str]:
        """
        Extract abbreviations from company names
        
        Args:
            company_names: List of company names
            
        Returns:
            Set of abbreviations found
        """
        abbreviations = set()
        
        for name in company_names:
            if not name:
                continue
                
            words = name.split()
            for word in words:
                # Check if word ends with period (likely abbreviation)
                if word.endswith("."):
                    abbreviations.add(word)
        
        return abbreviations
    
    def expand_abbreviation(self, abbreviation: str) -> str:
        """
        Expand a single abbreviation using Gemini AI
        
        Args:
            abbreviation: Abbreviation to expand
            
        Returns:
            Expanded form of the abbreviation
        """
        if abbreviation in self.abbreviation_map and self.abbreviation_map[abbreviation]:
            return self.abbreviation_map[abbreviation]
        
        try:
            prompt = f"Expand the company-related abbreviation '{abbreviation}' into its full form. Return only the expansion, no explanation."
            response = self.model.generate_content(prompt)
            expansion = response.text.strip()
            
            self.abbreviation_map[abbreviation] = expansion
            logger.info(f"✅ {abbreviation} → {expansion}")
            
            # Save progress after each expansion
            self.save_abbreviations()
            
            # Rate limiting - wait 3 seconds between API calls
            time.sleep(3)
            
            return expansion
            
        except Exception as e:
            logger.error(f"❌ Error expanding abbreviation {abbreviation}: {e}")
            self.abbreviation_map[abbreviation] = ""
            self.save_abbreviations()
            raise AbbreviationExpansionError(f"Failed to expand abbreviation: {abbreviation}", abbreviation)
    
    def expand_abbreviations_in_names(self, company_names: list) -> Dict[str, str]:
        """
        Expand abbreviations in a list of company names
        
        Args:
            company_names: List of company names
            
        Returns:
            Dictionary mapping original names to expanded names
        """
        expanded_names = {}
        abbreviations = self.extract_abbreviations(company_names)
        
        logger.info(f"Found {len(abbreviations)} abbreviations to expand")
        
        for abbreviation in abbreviations:
            try:
                expansion = self.expand_abbreviation(abbreviation)
                logger.info(f"Expanded {abbreviation} to {expansion}")
            except Exception as e:
                logger.error(f"Failed to expand {abbreviation}: {e}")
                continue
        
        # Now expand the company names
        for name in company_names:
            if not name:
                expanded_names[name] = name
                continue
                
            expanded_name = name
            for abbreviation, expansion in self.abbreviation_map.items():
                if abbreviation in expanded_name and expansion:
                    expanded_name = expanded_name.replace(abbreviation, expansion)
            
            expanded_names[name] = expanded_name
        
        return expanded_names
    
    def get_abbreviation_map(self) -> Dict[str, str]:
        """
        Get the current abbreviation mapping
        
        Returns:
            Dictionary of abbreviations and their expansions
        """
        return self.abbreviation_map.copy()
    
    def add_abbreviation(self, abbreviation: str, expansion: str):
        """
        Manually add an abbreviation and its expansion
        
        Args:
            abbreviation: The abbreviation
            expansion: The expansion
        """
        self.abbreviation_map[abbreviation] = expansion
        self.save_abbreviations()
        logger.info(f"Added abbreviation: {abbreviation} → {expansion}")
    
    def normalize_company_name(self, company_name: str) -> str:
        """
        Normalize a company name by expanding abbreviations
        
        Args:
            company_name: Company name to normalize
            
        Returns:
            Normalized company name
        """
        if not company_name:
            return company_name
        
        normalized_name = company_name
        for abbreviation, expansion in self.abbreviation_map.items():
            if abbreviation in normalized_name and expansion:
                normalized_name = normalized_name.replace(abbreviation, expansion)
        
        return normalized_name
    
    def match_company_names(self, name1: str, name2: str) -> bool:
        """
        Check if two company names match (after normalization)
        
        Args:
            name1: First company name
            name2: Second company name
            
        Returns:
            True if names match, False otherwise
        """
        if not name1 or not name2:
            return False
        
        # Normalize both names
        norm1 = self.normalize_company_name(name1).lower().strip()
        norm2 = self.normalize_company_name(name2).lower().strip()
        
        # Check for exact match
        if norm1 == norm2:
            return True
        
        # Check for partial match (one contains the other)
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        return False
