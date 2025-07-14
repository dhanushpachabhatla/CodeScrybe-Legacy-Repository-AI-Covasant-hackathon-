import os
import json
import time
import re
import tiktoken
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from google import genai
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ner_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CLAUDE_API_KEY = os.getenv("ANTHROPIC_CLAUDE_API_KEY")
PREFERRED_API = os.getenv("PREFERRED_API", "gemini").lower()  # Default to gemini

# Initialize clients
claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Configuration
INPUT_FILE = "pipeline_parsed_code.json"
OUTPUT_FILE = "pipeline_ner_output.json"
CACHE_FILE = "pipeline_ner_output_cache.json"
STATS_FILE = "pipeline_ner_stats.json"

# Enhanced token limits based on API
API_LIMITS = {
    "gemini": {"token_limit": 6000, "rate_limit": 1.2},
    "claude": {"token_limit": 8000, "rate_limit": 1.0}
}

# Initialize token encoder
encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")

def count_tokens(text: str) -> int:
    """Count tokens in text"""
    try:
        return len(encoder.encode(text))
    except Exception as e:
        logger.warning(f"Token counting error: {e}")
        return len(text) // 4  # Rough estimate

def get_api_response(prompt: str, temperature: float = 0.3, max_tokens: int = 4000) -> str:
    """Get response from preferred API with intelligent fallback"""
    try:
        if PREFERRED_API == "claude" and claude_client:
            logger.debug("Using Claude API")
            response = claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif PREFERRED_API == "gemini" and gemini_client:
            logger.debug("Using Gemini API")
            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            return response.text
        
        else:
            # Intelligent fallback to available API
            if gemini_client:
                logger.info("Falling back to Gemini API")
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                return response.text
            elif claude_client:
                logger.info("Falling back to Claude API")
                response = claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            else:
                raise Exception("No API keys available")
                
    except Exception as e:
        logger.error(f"Error with {PREFERRED_API} API: {e}")
        # Try fallback API
        try:
            if PREFERRED_API == "claude" and gemini_client:
                logger.info("Attempting Gemini fallback")
                response = gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                return response.text
            elif PREFERRED_API == "gemini" and claude_client:
                logger.info("Attempting Claude fallback")
                response = claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
        except Exception as fallback_error:
            logger.error(f"Fallback API also failed: {fallback_error}")
            raise Exception(f"Both APIs failed: {e}, {fallback_error}")

def create_enhanced_prompt(batch: List[Dict], context: Dict = None) -> str:
    """Create an enhanced, context-aware prompt for code analysis"""
    
    # Extract language statistics and patterns
    languages = list(set(chunk.get('language', 'unknown') for chunk in batch))
    total_lines = sum(len(chunk.get('code', '').split('\n')) for chunk in batch)
    
    # Build context information
    context_info = ""
    if context:
        context_info = f"""
REPOSITORY CONTEXT:
- Primary Languages: {', '.join(languages)}
- Code Complexity: {context.get('complexity', 'medium')}
- Total Lines in Batch: {total_lines}
- Analysis Focus: {context.get('focus', 'comprehensive')}
"""

    # Format code chunks with enhanced metadata
    formatted_chunks = []
    for i, chunk in enumerate(batch):
        lines_count = len(chunk.get('code', '').split('\n'))
        complexity_indicator = "🔴 Complex" if lines_count > 100 else "🟡 Medium" if lines_count > 50 else "🟢 Simple"
        
        formatted_chunk = f"""
---
📁 File: {chunk.get('file', 'unknown')}
🔢 Chunk ID: {chunk.get('chunk_id', 0)}
💻 Language: {chunk.get('language', 'unknown')}
📊 Complexity: {complexity_indicator} ({lines_count} lines)
🎯 Priority: {i+1}/{len(batch)}

{chunk.get('code', '# No code available')}
---"""
        formatted_chunks.append(formatted_chunk)
    
    chunks_text = "\n\n".join(formatted_chunks)
    
    return f"""
🚀 **ADVANCED CODE ANALYSIS SYSTEM** 🚀

You are an elite software architect and code analysis expert with deep knowledge of software engineering patterns, best practices, and system design. Your task is to perform comprehensive analysis of code segments and extract structured intelligence.

{context_info}

📋 **ANALYSIS REQUIREMENTS:**

For each code segment, provide detailed analysis in the following JSON structure:

```json
[
  {{
    "file": "exact_file_path",
    "chunk_id": 0,
    "language": "detected_language",
    "feature": "descriptive_feature_name",
    "description": "comprehensive_technical_description",
    "complexity_score": 0.85,
    "architecture_pattern": "mvc|repository|factory|singleton|observer|etc",
    "code_quality": {{
      "maintainability": 0.8,
      "readability": 0.7,
      "performance": 0.9,
      "security": 0.85
    }},
    "functions": [
      {{
        "name": "function_name",
        "signature": "complete_function_signature",
        "start_line": 10,
        "end_line": 25,
        "class": "enclosing_class_name_or_null",
        "visibility": "public|private|protected",
        "parameters": [
          {{
            "name": "param_name",
            "type": "param_type",
            "default_value": "default_or_null",
            "description": "parameter_purpose"
          }}
        ],
        "return_type": "return_type_or_void",
        "complexity": "low|medium|high",
        "purpose": "detailed_function_purpose",
        "side_effects": ["file_io", "network_calls", "state_changes"],
        "error_handling": "robust|basic|none"
      }}
    ],
    "classes": [
      {{
        "name": "class_name",
        "parent_class": "inheritance_chain",
        "interfaces": ["interface1", "interface2"],
        "design_pattern": "singleton|factory|observer|etc",
        "responsibility": "single_responsibility_description",
        "methods": [
          {{
            "name": "method_name",
            "visibility": "public|private|protected",
            "type": "constructor|getter|setter|business_logic|utility",
            "complexity": "low|medium|high"
          }}
        ],
        "properties": [
          {{
            "name": "property_name",
            "type": "property_type",
            "visibility": "public|private|protected",
            "purpose": "property_purpose"
          }}
        ]
      }}
    ],
    "apis": [
      {{
        "name": "api_name",
        "type": "rest|graphql|rpc|websocket|library",
        "endpoints": ["endpoint1", "endpoint2"],
        "authentication": "required|optional|none",
        "rate_limiting": "yes|no|unknown"
      }}
    ],
    "database_operations": [
      {{
        "type": "crud_operation",
        "tables": ["table1", "table2"],
        "queries": ["SELECT example", "INSERT example"],
        "orm_used": "sequelize|mongoose|prisma|raw_sql",
        "performance_concerns": ["n+1_queries", "missing_indexes"]
      }}
    ],
    "inputs": [
      {{
        "name": "input_name",
        "type": "user_input|file|network|database|environment",
        "validation": "strict|basic|none",
        "sanitization": "yes|no",
        "source": "specific_source_description"
      }}
    ],
    "outputs": [
      {{
        "name": "output_name",
        "type": "return_value|file|network|database|ui_update",
        "format": "json|html|csv|binary|etc",
        "destination": "specific_destination_description"
      }}
    ],
    "dependencies": [
      {{
        "name": "dependency_name",
        "type": "external_library|internal_module|system_service",
        "version": "version_if_available",
        "purpose": "why_this_dependency_is_needed",
        "criticality": "high|medium|low"
      }}
    ],
    "side_effects": [
      {{
        "type": "file_system|network|database|global_state|ui",
        "description": "detailed_side_effect_description",
        "impact": "high|medium|low",
        "mitigation": "how_to_handle_or_prevent"
      }}
    ],
    "requirements": [
      {{
        "type": "functional|non_functional|technical|business",
        "description": "requirement_description",
        "priority": "critical|high|medium|low",
        "implementation_status": "implemented|partial|missing"
      }}
    ],
    "security_analysis": {{
      "vulnerabilities": ["sql_injection", "xss", "csrf"],
      "authentication_required": true,
      "authorization_implemented": true,
      "data_encryption": "yes|no|partial",
      "input_validation": "comprehensive|basic|missing"
    }},
    "performance_metrics": {{
      "time_complexity": "O(n)",
      "space_complexity": "O(1)",
      "bottlenecks": ["database_queries", "file_operations"],
      "optimization_opportunities": ["caching", "async_processing"]
    }},
    "comments": [
      {{
        "content": "comment_text",
        "type": "inline|block|docstring|todo|fixme",
        "line_number": 15,
        "quality": "helpful|redundant|outdated",
        "sentiment": "positive|neutral|negative"
      }}
    ],
    "annotations": {{
      "developer_notes": "insights_and_observations",
      "code_smells": ["long_method", "large_class", "duplicate_code"],
      "refactoring_suggestions": ["extract_method", "introduce_parameter"],
      "testing_recommendations": ["unit_tests", "integration_tests"],
      "documentation_quality": "excellent|good|fair|poor",
      "maintainability_score": 0.85
    }},
    "integration_points": [
      {{
        "type": "service_call|event_listener|data_flow",
        "description": "how_this_code_integrates_with_system",
        "dependencies": ["service_a", "service_b"],
        "communication_protocol": "http|websocket|message_queue"
      }}
    ],
    "business_logic": {{
      "domain": "user_management|payment|inventory|etc",
      "rules": ["business_rule_1", "business_rule_2"],
      "workflows": ["workflow_step_1", "workflow_step_2"],
      "stakeholders": ["end_users", "administrators", "external_services"]
    }}
  }}
]
```

🎯 **QUALITY STANDARDS:**
- **Accuracy**: 95%+ precision in feature detection
- **Completeness**: Extract ALL relevant information
- **Consistency**: Maintain uniform analysis depth
- **Intelligence**: Provide actionable insights
- **Relevance**: Focus on business and technical value

⚡ **ADVANCED ANALYSIS FEATURES:**
- Detect architectural patterns and design principles
- Identify code quality metrics and technical debt
- Analyze security implications and vulnerabilities
- Assess performance characteristics and bottlenecks
- Evaluate maintainability and extensibility
- Recognize business logic and domain concepts

🔍 **CODE TO ANALYZE:**
{chunks_text}

🚨 **CRITICAL INSTRUCTIONS:**
1. Return ONLY valid JSON - no markdown, no explanations
2. Ensure all string values are properly escaped
3. Use null for missing/unknown values
4. Be thorough but concise in descriptions
5. Focus on actionable insights and practical value
6. Maintain consistent quality across all chunks

Begin analysis now:
""".strip()

def clean_json_string(text: str) -> str:
    """Enhanced JSON cleaning with better error handling"""
    try:
        # Remove markdown formatting
        if text.strip().startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text.strip())
        
        # Remove any leading/trailing whitespace
        text = text.strip()
        
        # Fix common JSON issues
        text = re.sub(r',\s*}', '}', text)  # Remove trailing commas in objects
        text = re.sub(r',\s*]', ']', text)  # Remove trailing commas in arrays
        
        # Ensure proper JSON structure
        if not text.startswith('[') and not text.startswith('{'):
            # Try to find JSON content
            json_match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
        
        return text
    except Exception as e:
        logger.error(f"JSON cleaning error: {e}")
        return text

def create_batch_hash(batch: List[Dict]) -> str:
    """Create a unique hash for a batch to enable smart caching"""
    batch_content = json.dumps(batch, sort_keys=True)
    return hashlib.md5(batch_content.encode()).hexdigest()

def enhanced_token_aware_batching(chunks: List[Dict], global_chunks: Dict) -> List[List[Dict]]:
    """Advanced batching with context awareness and optimization"""
    current_api = PREFERRED_API if (PREFERRED_API in API_LIMITS) else "gemini"
    token_limit = API_LIMITS[current_api]["token_limit"]
    
    batches = []
    current_batch = []
    
    # Sort chunks by complexity and importance
    def chunk_priority(chunk):
        code_length = len(chunk.get('code', ''))
        chunk_id = chunk.get('chunk_id', 0)
        # Prioritize main chunks (chunk_id 0) and larger code blocks
        return (0 if chunk_id == 0 else 1, -code_length)
    
    sorted_chunks = sorted(chunks, key=chunk_priority)
    
    for chunk in sorted_chunks:
        if chunk["chunk_id"] == 0:
            continue  # Handle global chunks separately
        
        file_global_chunk = global_chunks.get(chunk["file"])
        test_batch = current_batch + [chunk]
        
        # Calculate token count including global context
        code_blob = "\n\n".join([c['code'] for c in test_batch])
        if file_global_chunk and file_global_chunk not in test_batch:
            code_blob = file_global_chunk['code'] + "\n\n" + code_blob
        
        token_count = count_tokens(code_blob)
        
        # Enhanced batching logic
        if token_count > token_limit:
            if current_batch:
                batches.append(current_batch)
                logger.info(f"Batch created with {len(current_batch)} chunks, ~{token_count} tokens")
            current_batch = [chunk]
        else:
            current_batch.append(chunk)
    
    if current_batch:
        batches.append(current_batch)
        logger.info(f"Final batch created with {len(current_batch)} chunks")
    
    return batches

def process_batch_with_retry(batch: List[Dict], batch_id: str, max_retries: int = 3) -> Optional[List[Dict]]:
    """Process a batch with intelligent retry logic"""
    for attempt in range(max_retries):
        try:
            logger.info(f"Processing {batch_id} (attempt {attempt + 1}/{max_retries})")
            
            # Create enhanced context for this batch
            context = {
                "complexity": "high" if len(batch) > 5 else "medium",
                "focus": "comprehensive",
                "batch_id": batch_id
            }
            
            prompt = create_enhanced_prompt(batch, context)
            
            # Get response with appropriate timeout
            response = get_api_response(prompt, temperature=0.2, max_tokens=4000)
            
            # Clean and parse JSON
            cleaned_response = clean_json_string(response)
            parsed_json = json.loads(cleaned_response)
            
            # Validate response structure
            if not isinstance(parsed_json, list):
                raise ValueError("Response is not a list")
            
            # Merge original code back into results
            for item in parsed_json:
                file_name = item.get("file")
                chunk_id = item.get("chunk_id", 0)
                
                # Find matching chunk
                matching_chunk = next(
                    (c for c in batch if c.get("file") == file_name and c.get("chunk_id") == chunk_id),
                    None
                )
                
                if matching_chunk:
                    item["code"] = matching_chunk.get("code", "")
                    item["original_metadata"] = {
                        "file_size": len(matching_chunk.get("code", "")),
                        "processed_at": datetime.now().isoformat()
                    }
            
            logger.info(f"✅ Successfully processed {batch_id}")
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in {batch_id} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to parse JSON after {max_retries} attempts")
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Processing error in {batch_id} (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to process batch after {max_retries} attempts")
                return None
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return None

def save_processing_stats(stats: Dict):
    """Save detailed processing statistics"""
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)
        logger.info(f"Processing statistics saved to {STATS_FILE}")
    except Exception as e:
        logger.error(f"Error saving stats: {e}")

def run_ner_pipeline():
    """Enhanced NER pipeline with advanced features"""
    start_time = time.time()
    
    # Print startup information
    logger.info("🚀 Starting Enhanced NER Pipeline")
    logger.info(f"🔧 Preferred API: {PREFERRED_API.upper()}")
    logger.info(f"🤖 Available APIs: {'✅ Gemini' if gemini_client else '❌ Gemini'} | {'✅ Claude' if claude_client else '❌ Claude'}")
    
    try:
        # Load parsed code chunks
        logger.info(f"📂 Loading chunks from {INPUT_FILE}")
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        
        logger.info(f"📊 Loaded {len(chunks)} code chunks")
        
        # Load or initialize cache
        cache = {}
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            logger.info(f"💾 Loaded cache with {len(cache)} entries")
        
        # Initialize processing statistics
        stats = {
            "start_time": datetime.now().isoformat(),
            "total_chunks": len(chunks),
            "api_used": PREFERRED_API,
            "batches_processed": 0,
            "batches_cached": 0,
            "batches_failed": 0,
            "total_tokens_processed": 0,
            "processing_errors": []
        }
        
        results = []
        
        # Build global chunks map
        global_chunks = {c["file"]: c for c in chunks if c["chunk_id"] == 0}
        logger.info(f"🌍 Found {len(global_chunks)} global chunks")
        
        # Create optimized batches
        logger.info("🔄 Creating optimized batches...")
        batches = enhanced_token_aware_batching(chunks, global_chunks)
        
        logger.info(f"📦 Created {len(batches)} batches for processing")
        
        # Process batches with enhanced logic
        for i, batch in enumerate(batches):
            batch_id = f"batch_{i}"
            batch_hash = create_batch_hash(batch)
            cache_key = f"{batch_id}_{batch_hash}"
            
            # Check cache first
            if cache_key in cache:
                logger.info(f"✅ Using cached result for {batch_id}")
                results.extend(cache[cache_key])
                stats["batches_cached"] += 1
                continue
            
            # Add global context if needed
            file_global_chunk = global_chunks.get(batch[0]["file"])
            if file_global_chunk and file_global_chunk not in batch:
                batch = [file_global_chunk] + batch
            
            # Process batch with retry logic
            batch_result = process_batch_with_retry(batch, batch_id)
            
            if batch_result:
                results.extend(batch_result)
                
                # Update cache
                cache[cache_key] = batch_result
                with open(CACHE_FILE, "w") as f:
                    json.dump(cache, f, indent=2)
                
                stats["batches_processed"] += 1
                logger.info(f"💾 Cached result for {batch_id}")
            else:
                stats["batches_failed"] += 1
                stats["processing_errors"].append({
                    "batch_id": batch_id,
                    "error": "Failed to process after retries",
                    "timestamp": datetime.now().isoformat()
                })
                logger.error(f"❌ Failed to process {batch_id}")
            
            # Rate limiting
            current_api = PREFERRED_API if PREFERRED_API in API_LIMITS else "gemini"
            rate_limit = API_LIMITS[current_api]["rate_limit"]
            time.sleep(rate_limit)
        
        # Save final results
        logger.info(f"💾 Saving {len(results)} results to {OUTPUT_FILE}")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Calculate final statistics
        end_time = time.time()
        stats.update({
            "end_time": datetime.now().isoformat(),
            "total_processing_time": f"{end_time - start_time:.2f}s",
            "total_results": len(results),
            "success_rate": f"{((stats['batches_processed'] + stats['batches_cached']) / len(batches)) * 100:.1f}%",
            "average_batch_size": len(chunks) / len(batches) if batches else 0,
            "cache_hit_rate": f"{(stats['batches_cached'] / len(batches)) * 100:.1f}%" if batches else "0%"
        })
        
        # Save statistics
        save_processing_stats(stats)
        
        # Print final summary
        logger.info("\n" + "="*80)
        logger.info("🎉 ENHANCED NER PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("="*80)
        logger.info(f"📊 Total Results: {len(results)}")
        logger.info(f"⏱️  Processing Time: {stats['total_processing_time']}")
        logger.info(f"✅ Success Rate: {stats['success_rate']}")
        logger.info(f"💾 Cache Hit Rate: {stats['cache_hit_rate']}")
        logger.info(f"🤖 API Used: {PREFERRED_API.upper()}")
        logger.info(f"📁 Output File: {OUTPUT_FILE}")
        logger.info(f"📈 Statistics: {STATS_FILE}")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Pipeline failed with error: {e}")
        stats["pipeline_error"] = str(e)
        stats["end_time"] = datetime.now().isoformat()
        save_processing_stats(stats)
        return False

def validate_api_setup():
    """Validate API configuration and provide helpful feedback"""
    logger.info("🔍 Validating API Setup...")
    
    if not GEMINI_API_KEY and not CLAUDE_API_KEY:
        logger.error("❌ No API keys found! Please set GEMINI_API_KEY or ANTHROPIC_CLAUDE_API_KEY")
        return False
    
    if PREFERRED_API == "gemini" and not GEMINI_API_KEY:
        logger.warning("⚠️  Preferred API is Gemini but no key found. Will use Claude if available.")
    
    if PREFERRED_API == "claude" and not CLAUDE_API_KEY:
        logger.warning("⚠️  Preferred API is Claude but no key found. Will use Gemini if available.")
    
    # Test API connectivity
    try:
        test_response = get_api_response("Hello, this is a test. Respond with 'API_TEST_SUCCESS'", max_tokens=50)
        if "API_TEST_SUCCESS" in test_response:
            logger.info("✅ API connectivity verified")
            return True
        else:
            logger.warning("⚠️  API responded but test failed")
            return True  # Still proceed, might work for actual requests
    except Exception as e:
        logger.error(f"❌ API connectivity test failed: {e}")
        return False

if __name__ == "__main__":
    # Validate setup before running
    if not validate_api_setup():
        logger.error("❌ API setup validation failed. Please check your configuration.")
        exit(1)
    
    # Run the enhanced pipeline
    success = run_ner_pipeline()
    
    if success:
        logger.info("🎉 Pipeline completed successfully!")
        exit(0)
    else:
        logger.error("💥 Pipeline failed!")
        exit(1)