#!/usr/bin/env python3
"""
PubMed RAG Service for Literature Grounding
============================================
Fetches real medical literature from PubMed via NCBI E-utilities
to ground LLM explanations in actual scientific literature.

Free public API: https://www.ncbi.nlm.nih.gov/books/NBK25501/
Documentation: https://www.ncbi.nlm.nih.gov/books/NBK25499/

No API key required for light use (< 3 requests/second).
"""

import requests
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
import time
import re
from html import unescape

logger = logging.getLogger(__name__)

# NCBI E-utilities base URLs
PUBMED_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBMED_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Request configuration
REQUEST_TIMEOUT = 15
MAX_ABSTRACTS = 3
MAX_RETRIES = 2
RATE_LIMIT_DELAY = 0.34  # ~3 requests/second limit

# Search query templates for different query types
SEARCH_TEMPLATES = {
    'explain': [
        '"{drug}" toxicity mechanism',
        '"{drug}" adverse effects mechanism',
        '"{drug}" mechanism of toxicity',
        '"{drug}" pharmacology toxicology',
    ],
    'safety': [
        '"{drug}" safety profile',
        '"{drug}" adverse effects clinical',
        '"{drug}" toxicity human',
    ],
    'ddi': [
        '"{drug1}" "{drug2}" interaction',
        '"{drug1}" "{drug2}" drug interaction',
        '"{drug1}" "{drug2}" pharmacokinetics interaction',
    ],
    'target': [
        '"{drug}" target receptor',
        '"{drug}" mechanism of action receptor',
        '"{drug}" pharmacology target',
    ],
}

# Toxicity-related MeSH terms for filtering
TOXICITY_MESH_TERMS = {
    'Drug Toxicity',
    'Drug-Induced Liver Injury',
    'Cardiotoxicity',
    'Nephrotoxicity',
    'Neurotoxicity',
    'Hepatotoxicity',
    'Cardiac Arrhythmias, Drug-Induced',
    'Long QT Syndrome, Drug-Induced',
}


@dataclass
class PubMedArticle:
    """Represents a PubMed article with metadata."""
    pmid: str
    title: str
    abstract: str
    authors: List[str]
    journal: str
    pub_date: str
    doi: Optional[str] = None
    mesh_terms: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    
    def to_citation(self) -> str:
        """Format as citation string."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        return f"{authors_str}. {self.title}. {self.journal} ({self.pub_date}). PMID: {self.pmid}"
    
    def to_context_snippet(self, max_chars: int = 500) -> str:
        """Get abstract snippet for LLM context."""
        snippet = self.abstract[:max_chars]
        if len(self.abstract) > max_chars:
            snippet += "..."
        return f"[PMID:{self.pmid}] {snippet}"


@dataclass
class LiteratureSearchResult:
    """Result of a literature search."""
    query: str
    query_type: str
    articles: List[PubMedArticle]
    total_found: int
    search_time_ms: int
    cached: bool = False


class PubMedRAG:
    """
    PubMed Retrieval-Augmented Generation service.
    
    Features:
    - Searches PubMed via NCBI E-utilities (E-search + E-fetch)
    - Filters for toxicity/safety relevance
    - Caches results for performance
    - Returns structured articles for LLM context injection
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AnuDrishti/1.0 (PharmaGuard AI; mailto:research@example.com)'
        })
        self._cache = {}
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting (max 3 req/sec)."""
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict) -> Optional[requests.Response]:
        """Make HTTP request with retries and rate limiting."""
        for attempt in range(MAX_RETRIES):
            self._rate_limit()
            try:
                response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    time.sleep(2 ** attempt)
                else:
                    logger.warning(f"PubMed API error: {response.status_code}")
            except requests.Timeout:
                logger.warning(f"PubMed API timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"PubMed API request failed: {e}")
        return None
    
    def _build_search_query(self, query_type: str, **kwargs) -> str:
        """Build PubMed search query from template."""
        templates = SEARCH_TEMPLATES.get(query_type, SEARCH_TEMPLATES['explain'])
        query_parts = []
        for template in templates:
            try:
                query_parts.append(template.format(**kwargs))
            except KeyError:
                continue
        return " OR ".join(query_parts)
    
    def _search_pmids(self, query: str, max_results: int = MAX_ABSTRACTS) -> List[str]:
        """Search PubMed and return list of PMIDs."""
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results * 2,  # Fetch extra for filtering
            'retmode': 'json',
            'sort': 'relevance',
        }
        
        response = self._make_request(PUBMED_ESEARCH_URL, params)
        if not response:
            return []
        
        try:
            data = response.json()
            pmids = data.get('esearchresult', {}).get('idlist', [])
            return pmids[:max_results]
        except Exception as e:
            logger.error(f"Failed to parse ESearch response: {e}")
            return []
    
    def _fetch_articles(self, pmids: List[str]) -> List[PubMedArticle]:
        """Fetch full article details for given PMIDs."""
        if not pmids:
            return []
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract',
        }
        
        response = self._make_request(PUBMED_EFETCH_URL, params)
        if not response:
            return []
        
        articles = []
        try:
            root = ET.fromstring(response.content)
            for article_elem in root.findall('.//PubmedArticle'):
                article = self._parse_article(article_elem)
                if article:
                    articles.append(article)
        except ET.ParseError as e:
            logger.error(f"Failed to parse PubMed XML: {e}")
        
        return articles
    
    def _parse_article(self, elem) -> Optional[PubMedArticle]:
        """Parse PubMed XML article element."""
        try:
            # PMID
            pmid_elem = elem.find('.//PMID')
            pmid = pmid_elem.text if pmid_elem is not None else ""
            
            # Title
            title_elem = elem.find('.//ArticleTitle')
            title = (title_elem.text or "").strip() if title_elem is not None else ""
            
            # Abstract
            abstract_text = ""
            abstract_elem = elem.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                abstract_text = " ".join(abstract_elem.itertext()).strip()
            elif abstract_elem is None:
                # Try multiple AbstractText elements
                for abs_elem in elem.findall('.//AbstractText'):
                    if abs_elem.text:
                        abstract_text += " " + abs_elem.text.strip()
            
            # Authors
            authors = []
            for author_elem in elem.findall('.//Author'):
                last = author_elem.find('LastName')
                fore = author_elem.find('ForeName')
                if last is not None and fore is not None:
                    authors.append(f"{fore.text} {last.text}")
                elif last is not None and last.text is not None:
                    authors.append(last.text)
            
            # Journal
            journal_elem = elem.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else ""
            
            # Publication date
            pub_date = ""
            pub_date_elem = elem.find('.//PubDate')
            if pub_date_elem is not None:
                year = pub_date_elem.find('Year')
                month = pub_date_elem.find('Month')
                day = pub_date_elem.find('Day')
                parts = []
                if year is not None:
                    parts.append(year.text)
                if month is not None:
                    parts.append(month.text)
                if day is not None:
                    parts.append(day.text)
                pub_date = " ".join(parts)
            
            # DOI
            doi = None
            for id_elem in elem.findall('.//ArticleId'):
                if id_elem.get('IdType') == 'doi':
                    doi = id_elem.text
                    break
            
            # MeSH terms
            mesh_terms = []
            for mesh_elem in elem.findall('.//MeshHeading/DescriptorName'):
                if mesh_elem.text:
                    mesh_terms.append(mesh_elem.text)
            
            # Clean and unescape text
            title = unescape(title)
            abstract = unescape(abstract_text)
            
            # Calculate relevance score based on toxicity MeSH terms
            relevance = self._calculate_relevance(mesh_terms)
            
            return PubMedArticle(
                pmid=pmid,
                title=title,
                abstract=abstract,
                authors=authors,
                journal=journal,
                pub_date=pub_date,
                doi=doi,
                mesh_terms=mesh_terms,
                relevance_score=relevance
            )
        except Exception as e:
            logger.error(f"Failed to parse article: {e}")
            return None
    
    def _calculate_relevance(self, mesh_terms: List[str]) -> float:
        """Calculate relevance score based on toxicity-related MeSH terms."""
        score = 0.0
        for term in mesh_terms:
            if term in TOXICITY_MESH_TERMS:
                score += 1.0
            elif any(t in term for t in ['toxicity', 'adverse', 'poisoning', 'side effect']):
                score += 0.5
        return min(score, 5.0)  # Cap at 5.0
    
    def search_literature(self, 
                         query_type: str,
                         drug_name: Optional[str] = None,
                         drug1: Optional[str] = None,
                         drug2: Optional[str] = None,
                         smiles: Optional[str] = None,
                         max_results: int = MAX_ABSTRACTS) -> LiteratureSearchResult:
        """
        Main entry point: search PubMed for relevant literature.
        
        Args:
            query_type: 'explain', 'safety', 'ddi', 'target'
            drug_name: Single drug name
            drug1, drug2: Two drug names for DDI queries
            smiles: SMILES string (for novel compounds)
            max_results: Maximum articles to return
        
        Returns:
            LiteratureSearchResult with ranked articles
        """
        start_time = time.time()
        
        # Build query
        if query_type == 'ddi' and drug1 and drug2:
            query = self._build_search_query('ddi', drug1=drug1, drug2=drug2)
        elif query_type == 'target':
            query = self._build_search_query('target', drug=drug_name or "")
        elif query_type == 'safety':
            query = self._build_search_query('safety', drug=drug_name or "")
        else:
            query = self._build_search_query('explain', drug=drug_name or "")
        
        # Check cache
        cache_key = f"{query_type}:{query}"
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            cached_result.cached = True
            cached_result.search_time_ms = int((time.time() - start_time) * 1000)
            return cached_result
        
        # Search for PMIDs
        pmids = self._search_pmids(query, max_results * 2)
        
        if not pmids:
            return LiteratureSearchResult(
                query=query,
                query_type=query_type,
                articles=[],
                total_found=0,
                search_time_ms=int((time.time() - start_time) * 1000)
            )
        
        # Fetch articles
        articles = self._fetch_articles(pmids[:max_results])
        
        # Sort by relevance score (descending)
        articles.sort(key=lambda a: a.relevance_score, reverse=True)
        
        result = LiteratureSearchResult(
            query=query,
            query_type=query_type,
            articles=articles[:max_results],
            total_found=len(pmids),
            search_time_ms=int((time.time() - start_time) * 1000)
        )
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    def get_context_for_llm(self, result: LiteratureSearchResult, max_chars: int = 1500) -> str:
        """Format search results as context for LLM prompt."""
        if not result.articles:
            return "No relevant literature found in PubMed."
        
        context_parts = [
            f"LITERATURE EVIDENCE (PubMed search: {result.total_found} articles found):"
        ]
        
        for i, article in enumerate(result.articles, 1):
            snippet = article.to_context_snippet(400)
            context_parts.append(f"\n[{i}] {snippet}")
        
        context = "\n".join(context_parts)
        
        # Truncate if too long
        if len(context) > max_chars:
            context = context[:max_chars] + "... [truncated]"
        
        return context
    
    def clear_cache(self):
        """Clear the search cache."""
        self._cache.clear()


# Singleton instance
_pubmed_rag = None

def get_pubmed_rag() -> PubMedRAG:
    """Get or create singleton PubMedRAG instance."""
    global _pubmed_rag
    if _pubmed_rag is None:
        _pubmed_rag = PubMedRAG()
    return _pubmed_rag


if __name__ == "__main__":
    # Quick test
    rag = get_pubmed_rag()
    
    print("Testing PubMed RAG with Aspirin...")
    result = rag.search_literature('explain', drug_name='aspirin', max_results=3)
    print(f"Query: {result.query}")
    print(f"Found: {result.total_found}, Returned: {len(result.articles)}")
    print(f"Time: {result.search_time_ms}ms")
    
    for article in result.articles:
        print(f"\nPMID: {article.pmid}")
        print(f"Title: {article.title[:80]}...")
        print(f"Relevance: {article.relevance_score}")
        print(f"Abstract: {article.abstract[:200]}...")
    
    # Test context generation
    print("\n--- LLM Context ---")
    context = rag.get_context_for_llm(result)
    print(context[:500])