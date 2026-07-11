# pipeline.py
import asyncio
import aiohttp
import json
from ollama import AsyncClient
from config import OLLAMA_MODEL, CONCURRENCY_LIMIT, APPS_POOL
from schema import AppResearchResult

ollama_client = AsyncClient()

async def fetch_html_context(url: str) -> str:
    """Pass 2 Scraper: Fetches text elements from documentation pages to verify data accuracy."""
    if not url or not url.startswith("http"):
        return "No explicit URL source provided."
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=6) as response:
                if response.status == 200:
                    text = await response.text()
                    # Strip basic characters to maximize contextual window space
                    return text[:2000]
    except Exception:
        pass
    return "Web document unextractable due to anti-bot systems."

async def run_local_agent_pipeline(app: dict) -> dict:
    """Orchestrates local dual-pass structured research execution."""
    
    fallback_data = {
        "app_name": app['name'], "category": app['category'], 
        "one_liner": "Requires human research validation.",
        "auth_methods": ["Other"], "accessibility": "Gated", 
        "api_surface": "Unknown", "has_mcp_server": False, 
        "buildability_verdict": "Blocked", "primary_blocker": "Scraping failure",
        "evidence_url": f"https://{app['hint']}", "pass1_accuracy_delta": False
    }

    # --- PASS 1: SYSTEM INFERENCE DISCOVERY ---
    p1_prompt = (
        f"Analyze the application: {app['name']}. Hint website context: {app['hint']}. Category: {app['category']}.\n"
        "Generate a structured research profile mapping out its developer API surface, "
        "how authentication works (OAuth2 vs API Key vs Token), and if credentials can be obtained via a self-serve path."
    )
    
    try:
        p1_response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': p1_prompt}],
            format=AppResearchResult.model_json_schema(),
            options={'temperature': 0}
        )
        p1_data = AppResearchResult.model_validate_json(p1_response.message.content)
        
        # --- PASS 2: VERIFICATION SELF-CORRECTION LOOP ---
        live_page_text = await fetch_html_context(p1_data.evidence_url)
        
        p2_prompt = (
            f"Review this initial data profile for {app['name']}:\n{p1_data.json()}\n\n"
            f"Here is actual documentation page source context collected from their developer site:\n{live_page_text}\n\n"
            "Audit the initial fields. If you find text indicating a sales gate, partner restriction, custom token auth, "
            "or an immediate enterprise payment wall that contradicts the first pass, correct those fields immediately. "
            "Set pass1_accuracy_delta to true ONLY if you changed a value due to a detected mistake."
        )
        
        p2_response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': p2_prompt}],
            format=AppResearchResult.model_json_schema(),
            options={'temperature': 0}
        )
        
        final_validated = AppResearchResult.model_validate_json(p2_response.message.content)
        return final_validated.model_dump()

    except Exception as e:
        print(f"⚠️ Agent notice processing {app['name']}: {e}")
        return fallback_data

async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    async def task_wrapper(app):
        async with semaphore:
            print(f"🕵️ Agent processing: {app['name']}")
            return await run_local_agent_pipeline(app)
            
    print(f"🚀 Initializing Local Pipeline Execution via {OLLAMA_MODEL}...")
    tasks = [task_wrapper(app) for app in APPS_POOL]
    output_matrix = await asyncio.gather(*tasks)
    
    with open("raw_matrix.json", "w") as f:
        json.dump(output_matrix, f, indent=2)
    print("\n✅ Pipeline processing finished. Master data pipeline state saved to raw_matrix.json.")

if __name__ == "__main__":
    asyncio.run(main())