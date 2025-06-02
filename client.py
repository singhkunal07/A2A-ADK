#!/usr/bin/env python3
"""
Enhanced Decision Flow Client with Detailed Logging
"""

import asyncio
import json
import logging
from uuid import uuid4
import httpx
from typing import Optional, Dict, Any

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleDecisionFlowClient:
    """Simple client for interacting with Decision Flow Agents with detailed logging."""
    
    def __init__(self, router_url: str = "http://localhost:10000"):
        self.router_url = router_url

    def _build_request(self, user_message: str) -> Dict[str, Any]:
        """Build a proper A2A message request."""
        request_id = str(uuid4())
        message_id = str(uuid4())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [{
                        "kind": "text",
                        "text": user_message,
                        "metadata": {}
                    }],
                    "kind": "message",
                    "metadata": {}
                },
                "configuration": {
                    "acceptedOutputModes": ["text/plain", "text"],
                    "historyLength": 0,
                    "blocking": False
                },
                "metadata": {}
            }
        }
        
        # Log the complete request being sent
        logger.info("🚀 CLIENT: Building request for Router Agent")
        logger.info(f"📤 CLIENT: Request ID: {request_id}")
        logger.info(f"📤 CLIENT: Message ID: {message_id}")
        logger.info(f"📤 CLIENT: User Message: '{user_message}'")
        logger.debug(f"📤 CLIENT: Full JSON-RPC Request: {json.dumps(request, indent=2)}")
        
        return request

    async def send_request(self, user_message: str) -> Optional[str]:
        """Send request to Router Agent and get response."""
        try:
            # Build request payload
            payload = self._build_request(user_message)
            
            logger.info("🌐 CLIENT: Sending HTTP POST to Router Agent...")
            logger.info(f"🌐 CLIENT: Target URL: {self.router_url}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.router_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120.0  # Increased timeout
                )
                
                logger.info(f"📥 CLIENT: Received HTTP response - Status: {response.status_code}")
                logger.debug(f"📥 CLIENT: Response headers: {dict(response.headers)}")
                
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                logger.info("📥 CLIENT: Successfully parsed JSON response")
                logger.debug(f"📥 CLIENT: Full JSON-RPC Response: {json.dumps(result, indent=2)}")
                
                # Check for JSON-RPC error
                if "error" in result:
                    error = result["error"]
                    logger.error(f"❌ CLIENT: JSON-RPC Error received: {error.get('message', str(error))}")
                    if "data" in error:
                        logger.error(f"❌ CLIENT: Error details: {error['data']}")
                    return None
                
                # Handle success response
                if "result" in result:
                    result_data = result["result"]
                    logger.info("✅ CLIENT: JSON-RPC success result received")
                    logger.debug(f"✅ CLIENT: Result data type: {type(result_data)}")
                    
                    extracted_text = self._extract_text_from_result(result_data)
                    if extracted_text:
                        logger.info(f"✅ CLIENT: Extracted text ({len(extracted_text)} chars): {extracted_text[:100]}...")
                    else:
                        logger.warning("⚠️  CLIENT: No text could be extracted from result")
                    
                    return extracted_text
                
                logger.error("❌ CLIENT: No result field in JSON-RPC response")
                return None

        except httpx.HTTPStatusError as http_error:
            logger.error(f"❌ CLIENT: HTTP error {http_error.response.status_code}: {http_error}")
            logger.error(f"❌ CLIENT: Response content: {http_error.response.text}")
            return None
            
        except httpx.ReadTimeout:
            logger.error("❌ CLIENT: Request timed out waiting for response")
            return None
            
        except Exception as e:
            logger.error(f"❌ CLIENT: Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_text_from_result(self, result_data: Dict[str, Any]) -> Optional[str]:
        """Extract text from various A2A result formats."""
        logger.debug(f"🔍 CLIENT: Extracting text from result type: {type(result_data)}")
        
        if not isinstance(result_data, dict):
            return str(result_data)
        
        # Handle direct Message response
        if result_data.get("kind") == "message":
            logger.debug("🔍 CLIENT: Processing Message result")
            parts = result_data.get("parts", [])
            text_parts = []
            for part in parts:
                if isinstance(part, dict) and part.get("kind") == "text":
                    text_parts.append(part.get("text", ""))
            result = " ".join(text_parts) if text_parts else None
            logger.debug(f"🔍 CLIENT: Extracted from Message: {result}")
            return result
        
        # Handle Task response
        elif result_data.get("kind") == "task":
            logger.debug("🔍 CLIENT: Processing Task result")
            
            # Check task status message
            status = result_data.get("status", {})
            if status.get("message"):
                msg = status["message"]
                if isinstance(msg, dict) and msg.get("parts"):
                    text_parts = []
                    for part in msg["parts"]:
                        if isinstance(part, dict) and part.get("kind") == "text":
                            text_parts.append(part.get("text", ""))
                    if text_parts:
                        result = " ".join(text_parts)
                        logger.debug(f"🔍 CLIENT: Extracted from Task status: {result}")
                        return result
            
            # Check artifacts
            artifacts = result_data.get("artifacts", [])
            for artifact in artifacts:
                if isinstance(artifact, dict):
                    parts = artifact.get("parts", [])
                    text_parts = []
                    for part in parts:
                        if isinstance(part, dict) and part.get("kind") == "text":
                            text_parts.append(part.get("text", ""))
                    if text_parts:
                        result = " ".join(text_parts)
                        logger.debug(f"🔍 CLIENT: Extracted from Task artifact: {result}")
                        return result
            
            return "Task completed successfully."
        
        # Handle other formats
        logger.debug("🔍 CLIENT: Using string conversion for unknown format")
        return str(result_data)

async def main():
    """Main entry point for the client."""
    client = SimpleDecisionFlowClient()
    
    print("=" * 60)
    print("🚀 Enhanced Decision Flow Client with Detailed Logging")
    print("📋 Check console for detailed request/response logs")
    print("=" * 60)
    
    try:
        print("\n👤 Enter your request (or 'exit' to quit): ", end="", flush=True)
        user_input = input().strip()
        
        while user_input.lower() != "exit":
            if user_input:  # Only process non-empty input
                logger.info(f"👤 USER INPUT: '{user_input}'")
                response = await client.send_request(user_input)
                if response:
                    print(f"\n🤖 {response}\n")
                else:
                    print("\n❌ No response received from the agents\n")
            
            print("👤 Enter your request (or 'exit' to quit): ", end="", flush=True)
            user_input = input().strip()
            
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Thank you for using Decision Flow!")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())