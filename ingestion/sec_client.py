"""
SEC EDGAR Client
Handles data ingestion from SEC EDGAR with rate limiting and section extraction
"""

import time
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from loguru import logger
from ratelimit import limits, sleep_and_retry
from sec_edgar_downloader import Downloader

from config.settings import get_settings
from config.schemas import Filing, FilingSection


# All major SEC filing types
FILING_TYPES = {
    '10-K': 'Annual Report',
    '10-Q': 'Quarterly Report',
    '8-K': 'Current Report',
    '10-K/A': 'Annual Report Amendment',
    '10-Q/A': 'Quarterly Report Amendment',
    '4': 'Insider Trading',
    'S-1': 'IPO Registration',
    'S-3': 'Shelf Registration',
    'S-4': 'Merger/Acquisition Registration',
    'S-8': 'Employee Benefit Plan',
    'DEF 14A': 'Proxy Statement',
    'DEFM14A': 'Merger Proxy',
    '13D': 'Beneficial Ownership Report',
    '13G': 'Beneficial Ownership Report (Passive)',
    'SC 13D': 'Beneficial Ownership',
    'SC 13G': 'Beneficial Ownership (Passive)',
    '144': 'Notice of Sale of Restricted Securities',
    '3': 'Initial Statement of Beneficial Ownership',
    '5': 'Annual Statement of Changes in Beneficial Ownership',
    'EFFECT': 'Notice of Effectiveness'
}


class SECClient:
    """Client for SEC EDGAR filings with date-aware retrieval"""
    
    def __init__(self, email: Optional[str] = None):
        """
        Initialize SEC client with rate limiting
        
        Args:
            email: Email for SEC API (required by SEC)
        """
        settings = get_settings()
        self.email = email or "your-email@example.com"
        self.rate_limit = settings.sec_rate_limit
        self.base_url = "https://www.sec.gov"
        self.data_dir = settings.raw_data_dir / "sec"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # SEC requires a User-Agent header with contact info
        self.headers = {
            'User-Agent': f'FMNA Platform {self.email}',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'www.sec.gov'
        }
        
        # Initialize downloader
        self.downloader = Downloader(str(self.data_dir), email_address=self.email)
        
        # Track current date for filtering recent filings
        self.current_date = date.today()
        
        logger.info(f"SEC Client initialized with rate limit: {self.rate_limit}/sec")
        logger.info(f"Current date: {self.current_date}")
    
    @sleep_and_retry
    @limits(calls=10, period=1)  # SEC limit: 10 requests per second
    def _make_request(self, url: str) -> requests.Response:
        """
        Make rate-limited request to SEC
        
        Args:
            url: Full URL to request
            
        Returns:
            Response object
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"SEC request failed for {url}: {str(e)}")
            raise
    
    def get_company_cik(self, ticker: str) -> Optional[str]:
        """
        Get CIK number for a ticker symbol
        
        Args:
            ticker: Company ticker symbol
            
        Returns:
            CIK string or None
        """
        # Try JSON endpoint first (more reliable)
        try:
            url = "https://www.sec.gov/cgi-bin/browse-edgar"
            params = {
                'action': 'getcompany',
                'CIK': ticker,
                'type': '',
                'dateb': '',
                'owner': 'exclude',
                'count': '1',
                'output': 'atom'
            }
            
            response = self._make_request(url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()]))
            
            # Try parsing as XML
            soup = BeautifulSoup(response.content, 'xml')
            cik_tag = soup.find('cik')
            if not cik_tag:
                cik_tag = soup.find('CIK')
            
            if cik_tag:
                cik = cik_tag.text.strip().zfill(10)
                logger.info(f"Found CIK for {ticker}: {cik}")
                return cik
            
            # If XML parsing fails, try text search
            content_str = response.content.decode('utf-8', errors='ignore')
            import re
            cik_match = re.search(r'<cik>(\d+)</cik>', content_str, re.IGNORECASE)
            if cik_match:
                cik = cik_match.group(1).zfill(10)
                logger.info(f"Found CIK for {ticker}: {cik}")
                return cik
            
            logger.warning(f"No CIK found for ticker: {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting CIK for {ticker}: {str(e)}")
            return None
    
    def search_filings(
        self,
        cik: str,
        filing_type: str = "10-K",
        count: int = 10,
        before_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for company filings
        
        Args:
            cik: Company CIK number
            filing_type: Type of filing (10-K, 10-Q, 8-K, etc.)
            count: Number of results to return
            before_date: Filter filings before this date
            
        Returns:
            List of filing metadata
        """
        url = f"{self.base_url}/cgi-bin/browse-edgar"
        params = {
            'action': 'getcompany',
            'CIK': cik,
            'type': filing_type,
            'dateb': before_date.strftime('%Y%m%d') if before_date else '',
            'owner': 'exclude',
            'count': count,
            'output': 'atom'
        }
        
        try:
            response = self._make_request(url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()]))
            soup = BeautifulSoup(response.content, 'xml')
            
            filings = []
            for entry in soup.find_all('entry'):
                try:
                    filing_date = entry.find('filing-date').text if entry.find('filing-date') else None
                    filing_href = entry.find('filing-href').text if entry.find('filing-href') else None
                    accession = entry.find('accession-number').text if entry.find('accession-number') else None
                    
                    filings.append({
                        'cik': cik,
                        'filing_type': filing_type,
                        'filing_date': datetime.strptime(filing_date, '%Y-%m-%d').date() if filing_date else None,
                        'accession_number': accession,
                        'url': filing_href
                    })
                except Exception as e:
                    logger.error(f"Error parsing filing entry: {str(e)}")
                    continue
            
            logger.info(f"Found {len(filings)} {filing_type} filings for CIK {cik}")
            return filings
            
        except Exception as e:
            logger.error(f"Error searching filings for CIK {cik}: {str(e)}")
            return []
    
    def download_filing(self, cik: str, accession_number: str) -> Optional[str]:
        """
        Download filing document
        
        Args:
            cik: Company CIK
            accession_number: Filing accession number
            
        Returns:
            File path of downloaded document or None
        """
        # Format accession number for URL (remove dashes)
        accession_no_dashes = accession_number.replace('-', '')
        
        # Construct document URL
        url = f"{self.base_url}/Archives/edgar/data/{cik}/{accession_no_dashes}/{accession_number}.txt"
        
        try:
            response = self._make_request(url)
            
            # Save to file
            output_dir = self.data_dir / cik
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{accession_number}.txt"
            
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded filing {accession_number} to {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error downloading filing {accession_number}: {str(e)}")
            return None
    
    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract clean text from HTML filing
        
        Args:
            html_content: HTML content string
            
        Returns:
            Clean text
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_section_item_7(self, filing_text: str) -> Optional[str]:
        """
        Extract Item 7 (MD&A) from 10-K filing
        
        Args:
            filing_text: Full filing text
            
        Returns:
            Item 7 text or None
        """
        # Pattern to find Item 7
        patterns = [
            r'ITEM\s+7\.?\s+MANAGEMENT[\s\S]*?(?=ITEM\s+7A|ITEM\s+8|$)',
            r'Item\s+7\.?\s+Management[\s\S]*?(?=Item\s+7A|Item\s+8|$)',
            r'ITEM\s+7\b[\s\S]*?(?=ITEM\s+7A|ITEM\s+8|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filing_text, re.IGNORECASE)
            if match:
                logger.info("Found Item 7 (MD&A)")
                return match.group(0)
        
        logger.warning("Could not find Item 7 in filing")
        return None
    
    def extract_section_item_7a(self, filing_text: str) -> Optional[str]:
        """
        Extract Item 7A (Quantitative and Qualitative Disclosures) from 10-K
        
        Args:
            filing_text: Full filing text
            
        Returns:
            Item 7A text or None
        """
        patterns = [
            r'ITEM\s+7A\.?\s+QUANTITATIVE[\s\S]*?(?=ITEM\s+8|$)',
            r'Item\s+7A\.?\s+Quantitative[\s\S]*?(?=Item\s+8|$)',
            r'ITEM\s+7A\b[\s\S]*?(?=ITEM\s+8|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filing_text, re.IGNORECASE)
            if match:
                logger.info("Found Item 7A (Market Risk)")
                return match.group(0)
        
        logger.warning("Could not find Item 7A in filing")
        return None
    
    def extract_section_item_8(self, filing_text: str) -> Optional[str]:
        """
        Extract Item 8 (Financial Statements) from 10-K
        
        Args:
            filing_text: Full filing text
            
        Returns:
            Item 8 text or None
        """
        patterns = [
            r'ITEM\s+8\.?\s+FINANCIAL\s+STATEMENTS[\s\S]*?(?=ITEM\s+9|$)',
            r'Item\s+8\.?\s+Financial\s+Statements[\s\S]*?(?=Item\s+9|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filing_text, re.IGNORECASE)
            if match:
                logger.info("Found Item 8 (Financial Statements)")
                return match.group(0)
        
        logger.warning("Could not find Item 8 in filing")
        return None
    
    def extract_risk_factors(self, filing_text: str) -> Optional[str]:
        """
        Extract Item 1A (Risk Factors) from 10-K
        
        Args:
            filing_text: Full filing text
            
        Returns:
            Risk factors text or None
        """
        patterns = [
            r'ITEM\s+1A\.?\s+RISK\s+FACTORS[\s\S]*?(?=ITEM\s+1B|ITEM\s+2|$)',
            r'Item\s+1A\.?\s+Risk\s+Factors[\s\S]*?(?=Item\s+1B|Item\s+2|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filing_text, re.IGNORECASE)
            if match:
                logger.info("Found Item 1A (Risk Factors)")
                return match.group(0)
        
        logger.warning("Could not find Risk Factors in filing")
        return None
    
    def extract_all_sections(self, filing_text: str) -> Dict[str, Optional[str]]:
        """
        Extract all major sections from a 10-K filing
        
        Args:
            filing_text: Full filing text
            
        Returns:
            Dictionary of extracted sections
        """
        return {
            'item_1a_risk_factors': self.extract_risk_factors(filing_text),
            'item_7_mda': self.extract_section_item_7(filing_text),
            'item_7a_market_risk': self.extract_section_item_7a(filing_text),
            'item_8_financials': self.extract_section_item_8(filing_text)
        }
    
    def get_latest_filing(
        self,
        ticker: str,
        filing_type: str = "10-K"
    ) -> Optional[Filing]:
        """
        Get the latest filing for a company
        
        Args:
            ticker: Company ticker symbol
            filing_type: Type of filing
            
        Returns:
            Filing object or None
        """
        # First, get CIK
        cik = self.get_company_cik(ticker)
        if not cik:
            logger.error(f"Could not find CIK for {ticker}")
            return None
        
        # Search for filings
        filings = self.search_filings(cik, filing_type, count=1)
        if not filings:
            logger.error(f"No {filing_type} filings found for {ticker}")
            return None
        
        latest = filings[0]
        
        # Download the filing
        file_path = self.download_filing(cik, latest['accession_number'])
        if not file_path:
            return None
        
        # Read the file
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            full_text = f.read()
        
        # Extract clean text if HTML
        if '<html' in full_text.lower() or '<HTML' in full_text:
            clean_text = self.extract_text_from_html(full_text)
        else:
            clean_text = full_text
        
        # Extract sections
        sections = self.extract_all_sections(clean_text)
        
        # Create Filing object
        filing = Filing(
            filing_id=f"{cik}_{latest['accession_number']}",
            cik=cik,
            symbol=ticker,
            filing_type=filing_type,
            filing_date=latest['filing_date'],
            period_end=latest['filing_date'],  # TODO: Extract actual period end
            accession_number=latest['accession_number'],
            url=latest['url'],
            full_text=clean_text[:100000],  # Truncate for storage
            items_extracted=list(sections.keys()),
            processed=True
        )
        
        logger.info(f"Successfully processed {filing_type} for {ticker}")
        return filing
    
    def bulk_download_filings(
        self,
        ticker: str,
        filing_types: List[str] = ["10-K", "10-Q"],
        num_filings: int = 5
    ) -> List[Filing]:
        """
        Download multiple filings for a company
        
        Args:
            ticker: Company ticker symbol
            filing_types: List of filing types to download
            num_filings: Number of each filing type to download
            
        Returns:
            List of Filing objects
        """
        filings = []
        
        for filing_type in filing_types:
            logger.info(f"Downloading {num_filings} {filing_type} filings for {ticker}")
            
            cik = self.get_company_cik(ticker)
            if not cik:
                continue
            
            filing_list = self.search_filings(cik, filing_type, count=num_filings)
            
            for filing_meta in filing_list:
                try:
                    file_path = self.download_filing(cik, filing_meta['accession_number'])
                    if file_path:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            full_text = f.read()
                        
                        if '<html' in full_text.lower():
                            clean_text = self.extract_text_from_html(full_text)
                        else:
                            clean_text = full_text
                        
                        sections = self.extract_all_sections(clean_text)
                        
                        filing = Filing(
                            filing_id=f"{cik}_{filing_meta['accession_number']}",
                            cik=cik,
                            symbol=ticker,
                            filing_type=filing_type,
                            filing_date=filing_meta['filing_date'],
                            period_end=filing_meta['filing_date'],
                            accession_number=filing_meta['accession_number'],
                            url=filing_meta['url'],
                            full_text=clean_text[:100000],
                            items_extracted=list(sections.keys()),
                            processed=True
                        )
                        
                        filings.append(filing)
                        
                        # Rate limiting - be nice to SEC
                        time.sleep(0.2)
                        
                except Exception as e:
                    logger.error(f"Error processing filing {filing_meta.get('accession_number')}: {str(e)}")
                    continue
        
        logger.info(f"Downloaded {len(filings)} total filings for {ticker}")
        return filings
