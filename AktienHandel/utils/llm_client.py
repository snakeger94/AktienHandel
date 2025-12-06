import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import requests
import json
import config

class LLMClient:
    """
    Unified wrapper for AI providers.
    Supports both Google Gemini (cloud) and Ollama (local).
    Provider is selected via config.AI_PROVIDER.
    """
    def __init__(self):
        self.provider = config.AI_PROVIDER.lower()
        self.enabled = False
        
        if self.provider == 'cloud':
            self._init_gemini()
        elif self.provider == 'local':
            self._init_ollama()
        else:
            print(f"[LLM] WARNING: Invalid AI_PROVIDER '{config.AI_PROVIDER}'. Valid options: 'cloud', 'local'")
            print("[LLM] AI features disabled.")
    
    def _init_gemini(self):
        """Initialize Google Gemini cloud AI."""
        if config.GEMINI_API_KEY:
            genai.configure(api_key=config.GEMINI_API_KEY)
            
            # Configure safety settings to be more permissive for stock analysis
            self.safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.model = genai.GenerativeModel(
                'gemini-2.5-flash',
                safety_settings=self.safety_settings
            )
            self.enabled = True
            print("[LLM] Gemini Flash initialized (cloud AI)")
        else:
            print("[LLM] WARNING: No GEMINI_API_KEY found. AI features disabled.")
    
    def _init_ollama(self):
        """Initialize Ollama local AI."""
        try:
            # Test connection to Ollama
            response = requests.get(f"{config.LOCAL_AI_URL}/api/tags", timeout=2)
            if response.status_code == 200:
                self.enabled = True
                print(f"[LLM] Ollama initialized with model: {config.LOCAL_AI_MODEL} (local AI)")
            else:
                print(f"[LLM] WARNING: Ollama server responded with status {response.status_code}")
                print("[LLM] AI features disabled.")
        except requests.exceptions.RequestException as e:
            print(f"[LLM] WARNING: Could not connect to Ollama at {config.LOCAL_AI_URL}")
            print(f"[LLM] Error: {e}")
            print("[LLM] Make sure Ollama is installed and running.")
            print(f"[LLM] Install from: https://ollama.ai/")
            print(f"[LLM] Then run: ollama pull {config.LOCAL_AI_MODEL}")

    def generate(self, prompt, max_tokens=500):
        """
        Generate text from a prompt using the configured provider.
        
        Args:
            prompt (str): The prompt to send to the AI.
            max_tokens (int): Maximum tokens in response.
            
        Returns:
            str: The generated text, or None if disabled/error.
        """
        if not self.enabled:
            return "AI disabled (no provider configured)"
        
        if self.provider == 'cloud':
            return self._generate_gemini(prompt, max_tokens)
        elif self.provider == 'local':
            return self._generate_ollama(prompt, max_tokens)
        else:
            return None
    
    def _generate_gemini(self, prompt, max_tokens):
        """Generate response using Gemini cloud API."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
                safety_settings=self.safety_settings
            )
            
            # Check if response was blocked
            if not response.candidates:
                print("[LLM] Response blocked - no candidates returned")
                return None
            
            # Check finish reason
            finish_reason = response.candidates[0].finish_reason
            if finish_reason != 1:  # 1 = STOP (normal completion)
                print(f"[LLM] Response blocked. Finish reason: {finish_reason}")
                print(f"[LLM] Safety ratings: {response.candidates[0].safety_ratings}")
                return None
            
            return response.text
            
        except AttributeError as e:
            # Handle case where response.text is not available
            print(f"[LLM] Response structure error: {e}")
            return None
        except Exception as e:
            print(f"[LLM] Gemini error: {e}")
            return None
    
    def _generate_ollama(self, prompt, max_tokens):
        """Generate response using Ollama local API."""
        try:
            url = f"{config.LOCAL_AI_URL}/api/generate"
            payload = {
                "model": config.LOCAL_AI_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.7,
                }
            }
            
            response = requests.post(url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '')
            else:
                print(f"[LLM] Ollama API error: {response.status_code}")
                print(f"[LLM] Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("[LLM] Ollama request timed out")
            return None
        except Exception as e:
            print(f"[LLM] Ollama error: {e}")
            return None

