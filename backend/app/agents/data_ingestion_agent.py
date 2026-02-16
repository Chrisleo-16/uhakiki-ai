"""
Data Ingestion Agent - Handles secure API communication with external institutions
Retrieves verification history and aggregates data streams from HELB, KUCCPS, etc.
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import logging

from crewai import Agent, Task, LLM


@dataclass
class ExternalDataSource:
    """Configuration for external data sources"""
    name: str
    base_url: str
    api_key: str
    timeout: int = 30
    retry_attempts: int = 3


@dataclass
class IngestedData:
    """Structured data from external sources"""
    source: str
    data: Dict[str, Any]
    timestamp: datetime
    checksum: str
    data_quality: float  # 0-1 score
    completeness_score: float  # 0-1 score


class DataIngestionAgent:
    """
    Specialized agent for secure data ingestion from external institutions
    Handles API communication, data validation, and quality assessment
    """
    
    def __init__(self, llm: LLM, mock_mode: bool = True):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self.mock_mode = mock_mode  # Enable mock mode for testing
        
        # External institution endpoints
        self.data_sources = {
            "HELB": ExternalDataSource(
                name="Higher Education Loans Board",
                base_url="https://api.helb.go.ke/v1",
                api_key="HELB_API_KEY"  # Would be from secure config
            ),
            "KUCCPS": ExternalDataSource(
                name="Kenya Universities and Colleges Central Placement Service",
                base_url="https://api.kuccps.ac.ke/v1", 
                api_key="KUCCPS_API_KEY"
            ),
            "NEMIS": ExternalDataSource(
                name="National Education Management Information System",
                base_url="https://api.nemis.go.ke/v1",
                api_key="NEMIS_API_KEY"
            ),
            "KNDR": ExternalDataSource(
                name="Kenya National Digital Registry",
                base_url="https://api.kndr.go.ke/v1",
                api_key="KNDR_API_KEY"
            )
        }
        
        # Session for HTTP requests
        self.session = None
    
    def create_agent(self) -> Agent:
        """Create CrewAI agent for data ingestion"""
        return Agent(
            role='External Data Integration Specialist',
            goal='Securely retrieve and aggregate verification data from external institutions',
            backstory="""You are a secure data integration specialist responsible for retrieving
            student verification data from Kenyan government institutions. You ensure data integrity,
            validate API responses, and maintain secure communication channels. You handle sensitive
            personal data with utmost care and comply with Kenya Data Protection Act 2019.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    async def ingest_data(self, context) -> Dict[str, Any]:
        """
        Main data ingestion method
        Retrieves data from all configured external sources
        """
        print(f"📡 [DATA] Starting data ingestion for student {context.student_id}")
        
        # Mock mode for testing - return simulated data
        if self.mock_mode:
            return {
                "student_id": context.student_id,
                "national_id": context.national_id,
                "ingestion_timestamp": datetime.now().isoformat(),
                "sources": {
                    "HELB": {
                        "status": "active",
                        "loan_amount": 50000,
                        "disbursement_status": "completed"
                    },
                    "KUCCPS": {
                        "placement_status": "confirmed",
                        "institution_placed": "University of Nairobi",
                        "course": "Computer Science"
                    },
                    "NEMIS": {
                        "kcse_index": context.national_id[-8:],
                        "kcse_year": "2022",
                        "school_attended": "Alliance High School"
                    },
                    "KNDR": {
                        "identity_verified": True,
                        "date_of_birth": "2000-01-01",
                        "county": "Nairobi"
                    }
                },
                "data_quality": 0.95,
                "completeness": 0.98,
                "errors": []
            }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        ingestion_results = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # Concurrent data retrieval from all sources
        tasks = []
        for source_name, source_config in self.data_sources.items():
            task = self._retrieve_from_source(source_name, source_config, context)
            tasks.append(task)
        
        # Wait for all retrievals to complete
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                source_name = list(self.data_sources.keys())[i]
                
                if isinstance(result, Exception):
                    ingestion_results["errors"].append({
                        "source": source_name,
                        "error": str(result)
                    })
                    self.logger.error(f"Failed to retrieve from {source_name}: {result}")
                else:
                    ingestion_results["sources"][source_name] = result
            
            # Calculate overall data quality and completeness
            ingestion_results["data_quality"] = self._calculate_data_quality(
                ingestion_results["sources"]
            )
            ingestion_results["completeness"] = self._calculate_completeness(
                ingestion_results["sources"]
            )
            
        except Exception as e:
            self.logger.error(f"Data ingestion failed: {e}")
            ingestion_results["errors"].append({"general": str(e)})
        
        return ingestion_results
    
    async def _retrieve_from_source(
        self, 
        source_name: str, 
        source_config: ExternalDataSource, 
        context
    ) -> Optional[IngestedData]:
        """Retrieve data from a specific external source"""
        
        try:
            # Build API endpoint based on source type
            endpoint = self._build_endpoint(source_name, context)
            
            headers = {
                "Authorization": f"Bearer {source_config.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "UhakikiAI/1.0"
            }
            
            # Make API request with retries
            data = await self._make_api_request(
                source_config.base_url + endpoint,
                headers,
                source_config.timeout,
                source_config.retry_attempts
            )
            
            if not data:
                return None
            
            # Validate and process the data
            processed_data = self._process_source_data(source_name, data)
            
            # Calculate data quality metrics
            data_quality = self._assess_data_quality(processed_data)
            completeness = self._assess_completeness(processed_data, source_name)
            
            # Generate checksum for integrity verification
            checksum = self._generate_checksum(processed_data)
            
            return IngestedData(
                source=source_name,
                data=processed_data,
                timestamp=datetime.now(),
                checksum=checksum,
                data_quality=data_quality,
                completeness_score=completeness
            )
            
        except Exception as e:
            self.logger.error(f"Error retrieving from {source_name}: {e}")
            return None
    
    def _build_endpoint(self, source_name: str, context) -> str:
        """Build API endpoint for specific source and context"""
        
        if source_name == "HELB":
            return f"/students/{context.national_id}/loan-status"
        elif source_name == "KUCCPS":
            return f"/placements/{context.national_id}"
        elif source_name == "NEMIS":
            return f"/students/{context.national_id}/academic-history"
        elif source_name == "KNDR":
            return f"/citizens/{context.national_id}/verification"
        else:
            raise ValueError(f"Unknown data source: {source_name}")
    
    async def _make_api_request(
        self, 
        url: str, 
        headers: Dict[str, str], 
        timeout: int, 
        retries: int
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP API request with retry logic"""
        
        for attempt in range(retries):
            try:
                async with self.session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        self.logger.warning(f"Data not found at {url}")
                        return None
                    else:
                        self.logger.warning(f"API returned {response.status} from {url}")
                        
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
            except Exception as e:
                self.logger.error(f"Request failed on attempt {attempt + 1}: {e}")
            
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _process_source_data(self, source_name: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and standardize data from external source"""
        
        processed = {
            "source": source_name,
            "raw_data": raw_data,
            "processed_fields": {},
            "flags": [],
            "warnings": []
        }
        
        try:
            if source_name == "HELB":
                processed["processed_fields"] = {
                    "loan_status": raw_data.get("loan_status"),
                    "loan_amount": raw_data.get("approved_amount"),
                    "disbursement_status": raw_data.get("disbursement_status"),
                    "academic_year": raw_data.get("academic_year"),
                    "institution": raw_data.get("institution_name")
                }
                
                # Check for suspicious patterns
                if raw_data.get("loan_status") == "under_investigation":
                    processed["flags"].append("HELB_INVESTIGATION")
                
            elif source_name == "KUCCPS":
                processed["processed_fields"] = {
                    "placement_status": raw_data.get("placement_status"),
                    "institution_placed": raw_data.get("institution"),
                    "course": raw_data.get("course"),
                    "admission_number": raw_data.get("admission_no"),
                    "placement_year": raw_data.get("year")
                }
                
            elif source_name == "NEMIS":
                processed["processed_fields"] = {
                    "kcse_index": raw_data.get("kcse_index_number"),
                    "kcse_year": raw_data.get("kcse_year"),
                    "school_attended": raw_data.get("secondary_school"),
                    "exam_center": raw_data.get("examination_center")
                }
                
                # Validate KCSE details
                if not raw_data.get("kcse_index_number"):
                    processed["warnings"].append("MISSING_KCSE_INDEX")
                
            elif source_name == "KNDR":
                processed["processed_fields"] = {
                    "identity_verified": raw_data.get("verification_status"),
                    "date_of_birth": raw_data.get("dob"),
                    "county": raw_data.get("county"),
                    "constituency": raw_data.get("constituency")
                }
                
        except Exception as e:
            self.logger.error(f"Error processing {source_name} data: {e}")
            processed["errors"] = [str(e)]
        
        return processed
    
    def _assess_data_quality(self, processed_data: Dict[str, Any]) -> float:
        """Assess quality of ingested data"""
        
        if not processed_data:
            return 0.0
        
        quality_scores = []
        
        for source_name, data in processed_data.items():
            if isinstance(data, dict) and "processed_fields" in data:
                # Check for completeness of processed fields
                fields = data["processed_fields"]
                non_empty_fields = sum(1 for v in fields.values() if v is not None and v != "")
                total_fields = len(fields)
                
                if total_fields > 0:
                    field_completeness = non_empty_fields / total_fields
                    quality_scores.append(field_completeness)
                
                # Penalize sources with errors
                if "errors" in data:
                    quality_scores[-1] *= 0.5  # Reduce quality by 50% for errors
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _assess_completeness(self, processed_data: Dict[str, Any], source_name: str) -> float:
        """Assess completeness of data from specific source"""
        
        expected_fields = {
            "HELB": ["loan_status", "loan_amount", "disbursement_status"],
            "KUCCPS": ["placement_status", "institution_placed", "course"],
            "NEMIS": ["kcse_index", "kcse_year", "school_attended"],
            "KNDR": ["identity_verified", "date_of_birth", "county"]
        }
        
        if source_name not in expected_fields:
            return 0.5  # Default score for unknown sources
        
        source_data = processed_data.get(source_name)
        if not source_data or "processed_fields" not in source_data:
            return 0.0
        
        fields = source_data["processed_fields"]
        expected = expected_fields[source_name]
        
        non_empty_expected = sum(1 for field in expected if fields.get(field) is not None and fields.get(field) != "")
        
        return non_empty_expected / len(expected)
    
    def _calculate_data_quality(self, sources: Dict[str, Any]) -> float:
        """Calculate overall data quality score"""
        
        if not sources:
            return 0.0
        
        quality_scores = []
        
        for source_name, source_data in sources.items():
            if hasattr(source_data, 'data_quality'):
                quality_scores.append(source_data.data_quality)
        
        return sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
    
    def _calculate_completeness(self, sources: Dict[str, Any]) -> float:
        """Calculate overall data completeness score"""
        
        if not sources:
            return 0.0
        
        completeness_scores = []
        
        for source_name, source_data in sources.items():
            if hasattr(source_data, 'completeness_score'):
                completeness_scores.append(source_data.completeness_score)
        
        return sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
    
    def _generate_checksum(self, data: Dict[str, Any]) -> str:
        """Generate SHA-256 checksum for data integrity verification"""
        
        # Convert data to JSON string for hashing
        data_string = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
