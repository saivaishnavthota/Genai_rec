"""RAG service for hybrid retrieval and scoring"""
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import json
from ...config import settings
from ..models.kb_docs import KBDocument, KBBucket
from ..schemas.scoring import ScoreOut, CriteriaScore, Citation

logger = logging.getLogger(__name__)


class RAGService:
    """RAG service for hybrid retrieval and LLM-based scoring"""
    
    def __init__(self):
        self.ollama_url = settings.ollama_api_url
        self.ollama_model = settings.ollama_model
        self.top_k = settings.rag_top_k
        self.rerank_top_n = settings.rag_rerank_top_n
        self.hybrid_alpha = settings.rag_hybrid_alpha
    
    async def search_kb(
        self,
        db: Session,
        query: str,
        role: Optional[str] = None,
        level: Optional[str] = None,
        topic: Optional[str] = None,
        bucket: Optional[KBBucket] = None,
        top_k: Optional[int] = None
    ) -> List[KBDocument]:
        """
        Hybrid search: BM25 (full-text) + dense (vector) retrieval
        
        Args:
            db: Database session
            query: Search query
            role: Optional role filter
            level: Optional level filter
            topic: Optional topic filter
            bucket: Optional bucket filter
            top_k: Number of results
            
        Returns:
            List of KBDocument results
        """
        top_k = top_k or self.top_k
        
        # Build base query
        base_query = db.query(KBDocument)
        
        # Apply filters
        if role:
            base_query = base_query.filter(KBDocument.role == role)
        if level:
            base_query = base_query.filter(KBDocument.level == level)
        if topic:
            base_query = base_query.filter(KBDocument.topic == topic)
        if bucket:
            base_query = base_query.filter(KBDocument.bucket == bucket)
        
        # BM25 search using PostgreSQL full-text search
        # Note: This is simplified - in production, you'd use proper BM25 ranking
        bm25_query = base_query.filter(
            text("to_tsvector('english', text) @@ plainto_tsquery('english', :query)")
        ).params(query=query)
        
        # TODO: Add vector similarity search when embeddings are available
        # For now, use BM25 only
        results = bm25_query.limit(top_k).all()
        
        # If no BM25 results, fallback to simple text search
        if not results:
            results = base_query.filter(
                KBDocument.text.ilike(f"%{query}%")
            ).limit(top_k).all()
        
        return results
    
    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get embedding for text using Ollama (if available)
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Ollama embeddings endpoint
                response = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text}  # Use embedding model
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding")
        except Exception as e:
            logger.warning(f"Failed to get embedding: {e}")
        return None
    
    async def score_interview(
        self,
        db: Session,
        transcript: str,
        session_id: int,
        job_id: int
    ) -> ScoreOut:
        """
        Score interview using RAG + LLM
        
        Args:
            db: Database session
            transcript: Interview transcript
            session_id: Session ID
            job_id: Job ID
            
        Returns:
            ScoreOut with criteria, citations, and recommendation
        """
        # Get job details for context
        from ...models.job import Job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Search knowledge base for relevant rubric and exemplars
        search_queries = [
            f"{job.title} interview rubric",
            f"{job.experience_level} {job.title} evaluation criteria",
            "interview scoring rubric"
        ]
        
        all_docs = []
        for query in search_queries:
            docs = await self.search_kb(
                db,
                query,
                bucket=KBBucket.RUBRIC,
                top_k=3
            )
            all_docs.extend(docs)
        
        # Remove duplicates
        seen_ids = set()
        unique_docs = []
        for doc in all_docs:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                unique_docs.append(doc)
        
        # Build context from retrieved documents
        context = "\n\n".join([
            f"[Document {doc.id}]\n{doc.text}"
            for doc in unique_docs[:5]  # Limit context
        ])
        
        # Build scoring prompt
        prompt = f"""You are an expert interviewer evaluating a candidate's interview performance.

Job: {job.title}
Experience Level: {job.experience_level}
Key Skills: {', '.join(job.key_skills or [])}

Reference Rubric and Criteria:
{context}

Interview Transcript:
{transcript[:5000]}  # Limit transcript length

Evaluate the candidate based on the rubric and provide scores for each criterion.
Return a JSON object with this exact structure:
{{
  "criteria": [
    {{
      "criterion_name": "Technical Knowledge",
      "score": 8.5,
      "explanation": "Demonstrated strong understanding of core concepts...",
      "citations": [{{"doc_id": 1, "section": "Technical", "relevance_score": 0.9, "excerpt": "..."}}]
    }}
  ],
  "final_score": 8.2,
  "citations": [...],
  "summary": "Overall assessment...",
  "improvement_tip": "Could improve in..."
}}

Ensure all citations reference document IDs from the provided context.
"""
        
        # Call Ollama for scoring
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                logger.info(f"Calling Ollama at {self.ollama_url} with model {self.ollama_model}")
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": self.ollama_model,
                        "messages": [
                            {"role": "system", "content": "You are a precise JSON output generator. Return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 2000
                        },
                        "stream": False
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                if "message" in data and "content" in data["message"]:
                    content = data["message"]["content"]
                    # Parse JSON from response (may have markdown code blocks)
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    try:
                        score_data = json.loads(content)
                    except json.JSONDecodeError as json_err:
                        logger.error(f"Failed to parse JSON from Ollama response. Content: {content[:500]}")
                        raise ValueError(f"Invalid JSON response from LLM: {json_err}. Response preview: {content[:200]}")
                    
                    # Convert to ScoreOut schema
                    criteria = [
                        CriteriaScore(
                            criterion_name=c["criterion_name"],
                            score=Decimal(str(c["score"])),
                            explanation=c["explanation"],
                            citations=[
                                Citation(**cit) for cit in c.get("citations", [])
                            ]
                        )
                        for c in score_data.get("criteria", [])
                    ]
                    
                    citations = [
                        Citation(**c) for c in score_data.get("citations", [])
                    ]
                    
                    return ScoreOut(
                        criteria=criteria,
                        final_score=Decimal(str(score_data.get("final_score", 0))),
                        citations=citations,
                        summary=score_data.get("summary", ""),
                        improvement_tip=score_data.get("improvement_tip")
                    )
                else:
                    logger.error(f"Unexpected response format from Ollama: {data}")
                    raise ValueError(f"Unexpected response format from Ollama. Expected 'message.content', got: {list(data.keys())}")
        except httpx.ConnectError as e:
            logger.error(f"Connection error to Ollama at {self.ollama_url}: {e}")
            raise RuntimeError(f"Cannot connect to Ollama at {self.ollama_url}. Please ensure Ollama is running. Error: {e}")
        except httpx.TimeoutException as e:
            logger.error(f"Timeout calling Ollama: {e}")
            raise RuntimeError(f"Ollama request timed out after 300 seconds. The model may be too slow or Ollama may be overloaded. Error: {e}")
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Ollama returned HTTP {e.response.status_code}. Error: {e.response.text}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            raise RuntimeError(f"Failed to parse JSON response from Ollama: {e}")
        except Exception as e:
            logger.error(f"Scoring error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to score interview: {e}")

