"""
Simple tests for Security Service
"""
import pytest
from services.security_service import SecurityService
from core.exceptions import SecurityNotFoundError, InvalidInputError


class TestSecurityService:
    """Test cases for Security Service"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.security_service = SecurityService()
    
    def test_validate_security_data_valid(self):
        """Test validation with valid security data"""
        valid_data = {
            'isin_code': 'INE009A01021',
            'company_name': 'Test Company Ltd.',
            'nse_symbol': 'TEST',
            'bse_scrip_code': '123456'
        }
        
        result = self.security_service.validate_security_data(valid_data)
        assert result['valid'] is True
    
    def test_validate_security_data_missing_isin(self):
        """Test validation with missing ISIN code"""
        invalid_data = {
            'company_name': 'Test Company Ltd.',
            'nse_symbol': 'TEST'
        }
        
        with pytest.raises(InvalidInputError):
            self.security_service.validate_security_data(invalid_data)
    
    def test_validate_security_data_invalid_isin(self):
        """Test validation with invalid ISIN code"""
        invalid_data = {
            'isin_code': 'INVALID123',
            'company_name': 'Test Company Ltd.'
        }
        
        with pytest.raises(InvalidInputError):
            self.security_service.validate_security_data(invalid_data)
    
    def test_validate_security_data_invalid_numeric(self):
        """Test validation with invalid numeric field"""
        invalid_data = {
            'isin_code': 'INE009A01021',
            'company_name': 'Test Company Ltd.',
            'shares_outstanding_1': 'not_a_number'
        }
        
        with pytest.raises(InvalidInputError):
            self.security_service.validate_security_data(invalid_data)


class TestAbbreviationService:
    """Test cases for Abbreviation Service"""
    
    def setup_method(self):
        """Setup for each test method"""
        from services.abbreviation_service import AbbreviationService
        self.abbreviation_service = AbbreviationService()
    
    def test_extract_abbreviations(self):
        """Test abbreviation extraction from company names"""
        company_names = [
            "Infosys Ltd.",
            "Tata Motors Pvt. Ltd.",
            "Reliance Industries Ltd."
        ]
        
        abbreviations = self.abbreviation_service.extract_abbreviations(company_names)
        assert "Ltd." in abbreviations
        assert "Pvt." in abbreviations
    
    def test_normalize_company_name(self):
        """Test company name normalization"""
        # Add a test abbreviation
        self.abbreviation_service.add_abbreviation("Ltd.", "Limited")
        
        original_name = "Test Company Ltd."
        normalized_name = self.abbreviation_service.normalize_company_name(original_name)
        expected_name = "Test Company Limited"
        
        assert normalized_name == expected_name
    
    def test_match_company_names(self):
        """Test company name matching"""
        # Add test abbreviations
        self.abbreviation_service.add_abbreviation("Ltd.", "Limited")
        self.abbreviation_service.add_abbreviation("Pvt.", "Private")
        
        name1 = "Test Company Ltd."
        name2 = "Test Company Limited"
        
        assert self.abbreviation_service.match_company_names(name1, name2) is True
        
        name3 = "Different Company Pvt."
        assert self.abbreviation_service.match_company_names(name1, name3) is False


if __name__ == "__main__":
    pytest.main([__file__])
