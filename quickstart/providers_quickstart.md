# Universal LLM Providers Quickstart Guide 🤖

The Universal LLM Providers layer is your Swiss Army knife for AI integration. Write once, run on any LLM provider—OpenAI, Anthropic, Gemini, Ollama, or any future provider. It's the abstraction layer every AI-powered project needs.

## Table of Contents
- [Why Universal Providers?](#why-universal-providers)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported Providers](#supported-providers)
- [Core Features & Use Cases](#core-features--use-cases)
- [Real-World Examples](#real-world-examples)
- [Advanced Patterns](#advanced-patterns)
- [Best Practices](#best-practices)

## Why Universal Providers?

### The Problem
You built your app with OpenAI. Now you want to:
- Switch to Anthropic for better reasoning
- Use Gemini for cost savings
- Run locally with Ollama for privacy
- A/B test different models

**Traditional approach**: Rewrite half your codebase. **Universal Providers approach**: Change one config line.

### What Makes It Priceless

✅ **Single API Contract**: Write integration code once  
✅ **Zero Vendor Lock-in**: Switch providers in seconds  
✅ **Cost Optimization**: Compare providers without code changes  
✅ **Privacy Control**: Toggle between cloud and local models  
✅ **Future-Proof**: New providers? Just add an adapter  
✅ **Testability**: Mock providers for unit tests  

## Installation

```bash
# From the Modular_Utilities repository
cd providers
pip install -e .

# Or install from source
pip install git+https://github.com/justinlietz93/Modular_Utilities.git#subdirectory=providers
```

**Dependencies** (provider-specific):
```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For Google Gemini
pip install google-generativeai

# For Ollama (no extra deps, just install Ollama)
# Download from: https://ollama.ai
```

## Quick Start

### Basic Usage

```python
from providers import get_client
from providers.config import ProviderConfig

# Configure your provider
config = ProviderConfig(
    provider="openai",
    model="gpt-4o-mini",
    api_key="sk-..."  # Or set OPENAI_API_KEY env var
)

# Get the client
client = get_client(config)

# Make a request
response = client.complete("What is the meaning of life?")
print(response)
```

### Switch Providers (Zero Code Changes)

```python
# Originally using OpenAI
config = ProviderConfig(provider="openai", model="gpt-4o-mini", api_key=openai_key)

# Switch to Anthropic - SAME CODE!
config = ProviderConfig(provider="anthropic", model="claude-3-5-sonnet-20241022", api_key=anthropic_key)

# Or use Gemini
config = ProviderConfig(provider="gemini", model="gemini-2.0-flash-exp", api_key=gemini_key)

# Or go local with Ollama
config = ProviderConfig(provider="ollama", model="llama3.2", api_key=None)

# Client usage stays identical!
client = get_client(config)
response = client.complete("Same prompt, different provider!")
```

## Supported Providers

| Provider | Cloud/Local | Strengths | Use Case |
|----------|-------------|-----------|----------|
| **OpenAI** | Cloud | Fast, reliable, GPT-4o | Production apps, general AI |
| **Anthropic** | Cloud | Superior reasoning, longer context | Complex analysis, Claude-specific |
| **Gemini** | Cloud | Cost-effective, fast | Budget-conscious projects |
| **Ollama** | Local | Privacy, offline, free | Local-first, air-gapped systems |
| **OpenRouter** | Cloud | Multi-model access | Model experimentation |
| **DeepSeek** | Cloud | Specialized models | Domain-specific tasks |
| **xAI** | Cloud | Grok models | Emerging capabilities |

## Core Features & Use Cases

### 1. **Model Comparison & A/B Testing** 🧪

**Use Case**: Which model gives better code completions?

```python
from providers import get_client
from providers.config import ProviderConfig

# Define test models
models = [
    ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key),
    ProviderConfig(provider="anthropic", model="claude-3-5-sonnet-20241022", api_key=anthropic_key),
    ProviderConfig(provider="gemini", model="gemini-2.0-flash-exp", api_key=gemini_key),
]

prompt = "Write a Python function to calculate Fibonacci numbers efficiently."

# Test all models with the same prompt
results = {}
for config in models:
    client = get_client(config)
    response = client.complete(prompt)
    results[f"{config.provider}/{config.model}"] = response

# Compare results
for model, response in results.items():
    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print(f"{'='*60}")
    print(response)
```

**Workflow Integration**:
- Run weekly comparisons
- Track model performance over time
- Make data-driven provider decisions

### 2. **Cost Optimization** 💰

**Use Case**: OpenAI is expensive for your use case. Let's optimize!

```python
from providers import get_client
from providers.config import ProviderConfig
import time

def estimate_cost(config, prompt, num_calls=1000):
    """Estimate cost for N calls to a provider."""
    client = get_client(config)
    
    start = time.time()
    # Sample call to estimate tokens
    sample_response = client.complete(prompt)
    end = time.time()
    
    # Approximate costs (update with real pricing)
    costs_per_1k_tokens = {
        "openai/gpt-4o": 0.03,
        "anthropic/claude-3-5-sonnet-20241022": 0.015,
        "gemini/gemini-2.0-flash-exp": 0.0007,
        "ollama/llama3.2": 0.0,  # Local = free!
    }
    
    model_key = f"{config.provider}/{config.model}"
    cost_per_call = costs_per_1k_tokens.get(model_key, 0.01)
    total_cost = cost_per_call * num_calls / 1000
    
    return {
        "model": model_key,
        "cost_per_call": cost_per_call,
        "total_cost": total_cost,
        "latency": end - start
    }

# Compare costs across providers
prompt = "Summarize this document in 3 sentences."
providers_to_test = [
    ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key),
    ProviderConfig(provider="gemini", model="gemini-2.0-flash-exp", api_key=gemini_key),
    ProviderConfig(provider="ollama", model="llama3.2"),
]

print("Cost Analysis for 1000 calls:")
print("-" * 60)
for config in providers_to_test:
    estimate = estimate_cost(config, prompt, num_calls=1000)
    print(f"{estimate['model']}")
    print(f"  Cost: ${estimate['total_cost']:.2f}")
    print(f"  Latency: {estimate['latency']:.2f}s")
    print()
```

**Result**: Switch to Gemini, save 95% on costs!

### 3. **Privacy-First Local Models** 🔒

**Use Case**: Processing sensitive data (medical, financial, legal).

```python
from providers import get_client
from providers.config import ProviderConfig

# Use Ollama for 100% local processing
config = ProviderConfig(
    provider="ollama",
    model="llama3.2",  # Runs entirely on your machine
)

client = get_client(config)

# Process sensitive data without sending to cloud
sensitive_prompt = """
Analyze this patient record:
- Name: John Doe
- Diagnosis: ...
- Treatment: ...
"""

response = client.complete(sensitive_prompt)
# Data never leaves your machine! 🛡️
```

**Setup Ollama**:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2

# Verify it's running
ollama list
```

### 4. **Fallback & Retry Logic** 🔄

**Use Case**: OpenAI is down. Auto-fallback to Claude.

```python
from providers import get_client
from providers.config import ProviderConfig
from providers.exceptions import ProviderError

def complete_with_fallback(prompt, providers_config):
    """Try each provider until one succeeds."""
    for config in providers_config:
        try:
            client = get_client(config)
            response = client.complete(prompt)
            print(f"✅ Success with {config.provider}/{config.model}")
            return response
        except ProviderError as e:
            print(f"❌ Failed with {config.provider}: {e}")
            continue
    raise Exception("All providers failed!")

# Define fallback chain
fallback_chain = [
    ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key),
    ProviderConfig(provider="anthropic", model="claude-3-5-sonnet-20241022", api_key=anthropic_key),
    ProviderConfig(provider="ollama", model="llama3.2"),  # Last resort: local
]

# Make resilient request
response = complete_with_fallback("What is 2+2?", fallback_chain)
```

**CI/CD Integration**:
```yaml
# GitHub Actions example
env:
  PRIMARY_PROVIDER: openai
  FALLBACK_PROVIDER: ollama
```

### 5. **Model-Specific Parameters** ⚙️

**Use Case**: Fine-tune behavior for specific providers.

```python
from providers import get_client
from providers.config import ProviderConfig

# OpenAI with custom parameters
openai_config = ProviderConfig(
    provider="openai",
    model="gpt-4o",
    api_key=openai_key,
    temperature=0.7,
    max_tokens=500,
    top_p=0.9
)

# Anthropic with different settings
anthropic_config = ProviderConfig(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",
    api_key=anthropic_key,
    temperature=0.3,  # Lower for more deterministic
    max_tokens=1000
)

# Usage stays the same!
client = get_client(openai_config)
response = client.complete("Generate creative story ideas")
```

### 6. **Batch Processing** 📦

**Use Case**: Process 1000 prompts efficiently.

```python
from providers import get_client
from providers.config import ProviderConfig
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_complete(prompts, config, max_workers=10):
    """Process multiple prompts in parallel."""
    client = get_client(config)
    
    def process_one(prompt):
        return client.complete(prompt)
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_one, p): p for p in prompts}
        for future in as_completed(futures):
            prompt = futures[future]
            try:
                result = future.result()
                results.append({"prompt": prompt, "response": result})
            except Exception as e:
                results.append({"prompt": prompt, "error": str(e)})
    
    return results

# Process batch
prompts = [
    "Summarize article 1",
    "Summarize article 2",
    # ... 1000 more
]

config = ProviderConfig(provider="gemini", model="gemini-2.0-flash-exp", api_key=gemini_key)
results = batch_complete(prompts, config)

print(f"Processed {len(results)} prompts")
```

### 7. **Streaming Responses** 🌊

**Use Case**: Show real-time responses (chatbots, CLI tools).

```python
from providers import get_client
from providers.config import ProviderConfig

config = ProviderConfig(
    provider="openai",
    model="gpt-4o",
    api_key=openai_key,
    stream=True
)

client = get_client(config)

# Stream response
print("Assistant: ", end="", flush=True)
for chunk in client.complete_stream("Write a haiku about coding"):
    print(chunk, end="", flush=True)
print()  # Newline at end
```

**CLI Example**:
```python
import sys

def chat_loop(config):
    client = get_client(config)
    
    while True:
        prompt = input("\nYou: ")
        if prompt.lower() in ["exit", "quit"]:
            break
        
        print("Assistant: ", end="", flush=True)
        for chunk in client.complete_stream(prompt):
            print(chunk, end="", flush=True)
        print()

# Run interactive chat
config = ProviderConfig(provider="anthropic", model="claude-3-5-sonnet-20241022", api_key=anthropic_key)
chat_loop(config)
```

## Real-World Examples

### Example 1: Smart Documentation Generator

```python
from providers import get_client
from providers.config import ProviderConfig
import os

class DocumentationGenerator:
    def __init__(self, provider="openai", model="gpt-4o"):
        self.config = ProviderConfig(
            provider=provider,
            model=model,
            api_key=os.getenv(f"{provider.upper()}_API_KEY")
        )
        self.client = get_client(self.config)
    
    def document_function(self, code):
        prompt = f"""
        Generate comprehensive documentation for this function:
        
        ```python
        {code}
        ```
        
        Include:
        - Purpose
        - Parameters
        - Return value
        - Example usage
        """
        return self.client.complete(prompt)
    
    def generate_readme(self, codebase_summary):
        prompt = f"""
        Generate a README.md for this project:
        {codebase_summary}
        
        Include:
        - Project description
        - Installation
        - Usage examples
        - Contributing guidelines
        """
        return self.client.complete(prompt)

# Use it
gen = DocumentationGenerator(provider="gemini", model="gemini-2.0-flash-exp")

# Document a function
code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""

docs = gen.document_function(code)
print(docs)
```

### Example 2: Multi-Provider Code Review Bot

```python
from providers import get_client
from providers.config import ProviderConfig
import difflib

class CodeReviewBot:
    def __init__(self):
        # Use multiple providers for diverse feedback
        self.reviewers = {
            "openai": get_client(ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key)),
            "anthropic": get_client(ProviderConfig(provider="anthropic", model="claude-3-5-sonnet-20241022", api_key=anthropic_key)),
        }
    
    def review_diff(self, diff):
        prompt = f"""
        Review this code diff and provide feedback on:
        - Bugs
        - Performance issues
        - Security vulnerabilities
        - Style improvements
        
        Diff:
        {diff}
        """
        
        reviews = {}
        for name, client in self.reviewers.items():
            reviews[name] = client.complete(prompt)
        
        return reviews
    
    def consensus_review(self, diff):
        """Get reviews from multiple providers and synthesize."""
        reviews = self.review_diff(diff)
        
        # Synthesize with primary model
        synthesis_prompt = f"""
        Multiple AI models reviewed the same code. Synthesize their feedback:
        
        OpenAI: {reviews['openai']}
        
        Anthropic: {reviews['anthropic']}
        
        Provide a single, actionable review.
        """
        
        synthesizer = get_client(ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key))
        return synthesizer.complete(synthesis_prompt)

# Use it in PR workflow
bot = CodeReviewBot()
diff = """
+ def process_payment(amount, card_number):
+     # Process payment
+     return True
"""

review = bot.consensus_review(diff)
print(review)
```

### Example 3: Local-First Translation Service

```python
from providers import get_client
from providers.config import ProviderConfig

class TranslationService:
    def __init__(self, use_local=True):
        if use_local:
            # Privacy-first: use local Ollama
            config = ProviderConfig(provider="ollama", model="llama3.2")
        else:
            # Cloud-based for better quality
            config = ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key)
        
        self.client = get_client(config)
    
    def translate(self, text, target_language):
        prompt = f"Translate this to {target_language}:\n\n{text}"
        return self.client.complete(prompt)
    
    def batch_translate(self, texts, target_language):
        return [self.translate(t, target_language) for t in texts]

# Use local for sensitive content
local_translator = TranslationService(use_local=True)
sensitive_text = "Patient diagnosis: ..."
translation = local_translator.translate(sensitive_text, "Spanish")
# Never sent to cloud!

# Use cloud for better quality on public content
cloud_translator = TranslationService(use_local=False)
public_text = "Welcome to our website"
translation = cloud_translator.translate(public_text, "French")
```

## Advanced Patterns

### Pattern 1: Provider Router (Load Balancing)

```python
from providers import get_client
from providers.config import ProviderConfig
import random

class ProviderRouter:
    """Distribute load across multiple providers."""
    
    def __init__(self, providers_config):
        self.clients = [(config, get_client(config)) for config in providers_config]
    
    def complete(self, prompt, strategy="round_robin"):
        if strategy == "round_robin":
            return self._round_robin(prompt)
        elif strategy == "random":
            return self._random(prompt)
        elif strategy == "cheapest_first":
            return self._cheapest_first(prompt)
    
    def _round_robin(self, prompt):
        # Rotate through providers
        config, client = self.clients[self._counter % len(self.clients)]
        self._counter += 1
        return client.complete(prompt)
    
    def _random(self, prompt):
        config, client = random.choice(self.clients)
        return client.complete(prompt)
    
    def _cheapest_first(self, prompt):
        # Always use cheapest available provider
        # (Assume clients are sorted by cost)
        config, client = self.clients[0]
        return client.complete(prompt)

# Configure multiple providers
providers = [
    ProviderConfig(provider="gemini", model="gemini-2.0-flash-exp", api_key=gemini_key),  # Cheapest
    ProviderConfig(provider="openai", model="gpt-4o-mini", api_key=openai_key),
]

router = ProviderRouter(providers)

# Distribute load
for i in range(10):
    response = router.complete(f"Request {i}", strategy="round_robin")
```

### Pattern 2: Caching Layer

```python
from providers import get_client
from providers.config import ProviderConfig
import hashlib
import json
from pathlib import Path

class CachedProvider:
    """Cache responses to avoid redundant API calls."""
    
    def __init__(self, config, cache_dir=".provider_cache"):
        self.client = get_client(config)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _cache_key(self, prompt):
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def complete(self, prompt):
        cache_key = self._cache_key(prompt)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        # Check cache
        if cache_file.exists():
            with open(cache_file) as f:
                cached = json.load(f)
                print("✅ Cache hit!")
                return cached["response"]
        
        # Make request
        response = self.client.complete(prompt)
        
        # Save to cache
        with open(cache_file, "w") as f:
            json.dump({"prompt": prompt, "response": response}, f)
        
        return response

# Use cached provider
config = ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key)
cached_client = CachedProvider(config)

# First call: hits API
response1 = cached_client.complete("What is 2+2?")

# Second call: uses cache
response2 = cached_client.complete("What is 2+2?")  # ✅ Cache hit!
```

### Pattern 3: Provider Monitoring

```python
from providers import get_client
from providers.config import ProviderConfig
import time
import json

class MonitoredProvider:
    """Track latency, errors, and costs."""
    
    def __init__(self, config):
        self.client = get_client(config)
        self.config = config
        self.stats = {
            "total_calls": 0,
            "total_errors": 0,
            "total_latency": 0,
            "errors": []
        }
    
    def complete(self, prompt):
        start = time.time()
        try:
            response = self.client.complete(prompt)
            latency = time.time() - start
            
            self.stats["total_calls"] += 1
            self.stats["total_latency"] += latency
            
            return response
        except Exception as e:
            self.stats["total_errors"] += 1
            self.stats["errors"].append({
                "error": str(e),
                "timestamp": time.time()
            })
            raise
    
    def get_stats(self):
        avg_latency = self.stats["total_latency"] / max(self.stats["total_calls"], 1)
        return {
            "provider": f"{self.config.provider}/{self.config.model}",
            "total_calls": self.stats["total_calls"],
            "total_errors": self.stats["total_errors"],
            "avg_latency": f"{avg_latency:.2f}s",
            "error_rate": f"{self.stats['total_errors'] / max(self.stats['total_calls'], 1) * 100:.1f}%"
        }

# Monitor provider performance
config = ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key)
monitored_client = MonitoredProvider(config)

# Make requests
for i in range(10):
    try:
        monitored_client.complete(f"Request {i}")
    except:
        pass

# Check stats
print(json.dumps(monitored_client.get_stats(), indent=2))
```

## Best Practices

### ✅ DO: Use Environment Variables for API Keys

```python
import os
from providers.config import ProviderConfig

# ✅ Good
config = ProviderConfig(
    provider="openai",
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY")
)

# ❌ Bad
config = ProviderConfig(
    provider="openai",
    model="gpt-4o",
    api_key="sk-hardcoded-key-here"  # NEVER DO THIS!
)
```

### ✅ DO: Handle Errors Gracefully

```python
from providers.exceptions import ProviderError

try:
    client = get_client(config)
    response = client.complete(prompt)
except ProviderError as e:
    print(f"Provider error: {e}")
    # Fallback logic here
except Exception as e:
    print(f"Unexpected error: {e}")
```

### ✅ DO: Test with Multiple Providers

```python
import pytest
from providers import get_client
from providers.config import ProviderConfig

@pytest.mark.parametrize("provider,model", [
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-3-5-sonnet-20241022"),
    ("gemini", "gemini-2.0-flash-exp"),
])
def test_provider_completion(provider, model):
    config = ProviderConfig(provider=provider, model=model, api_key=get_api_key(provider))
    client = get_client(config)
    response = client.complete("Test prompt")
    assert response is not None
```

### ✅ DO: Use Model Registry for Discovery

```python
from providers.ollama import get_ollama_models
from providers.gemini import get_gemini_models

# Discover available models
ollama_models = get_ollama_models()
print(f"Available Ollama models: {ollama_models}")

gemini_models = get_gemini_models()
print(f"Available Gemini models: {gemini_models}")
```

### ❌ DON'T: Hardcode Provider Logic

```python
# ❌ Bad: Provider-specific code
if provider == "openai":
    client = OpenAI(api_key=key)
    response = client.chat.completions.create(...)
elif provider == "anthropic":
    client = Anthropic(api_key=key)
    response = client.messages.create(...)

# ✅ Good: Universal interface
client = get_client(config)
response = client.complete(prompt)
```

## Configuration Examples

### Example 1: Development vs Production

```python
import os

def get_provider_config(environment):
    if environment == "development":
        # Use local Ollama for free dev
        return ProviderConfig(
            provider="ollama",
            model="llama3.2"
        )
    elif environment == "production":
        # Use OpenAI for quality
        return ProviderConfig(
            provider="openai",
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY")
        )

config = get_provider_config(os.getenv("ENV", "development"))
client = get_client(config)
```

### Example 2: Feature Flags

```python
FEATURE_FLAGS = {
    "use_local_models": True,
    "enable_streaming": False,
    "max_retries": 3
}

if FEATURE_FLAGS["use_local_models"]:
    config = ProviderConfig(provider="ollama", model="llama3.2")
else:
    config = ProviderConfig(provider="openai", model="gpt-4o", api_key=openai_key)

if FEATURE_FLAGS["enable_streaming"]:
    config.stream = True
```

## Troubleshooting

### Issue: "Provider not found"
**Solution**: Check spelling and installation
```bash
pip list | grep openai  # Or anthropic, google-generativeai
```

### Issue: "API key invalid"
**Solution**: Verify environment variables
```bash
echo $OPENAI_API_KEY
# Should print: sk-...
```

### Issue: "Rate limit exceeded"
**Solution**: Implement exponential backoff
```python
import time

def complete_with_backoff(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.complete(prompt)
        except ProviderError as e:
            if "rate_limit" in str(e).lower():
                wait_time = 2 ** attempt
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

### Issue: "Ollama not responding"
**Solution**: Check if Ollama is running
```bash
ollama list
# If not: ollama serve
```

## Next Steps

1. **Experiment**: Try all providers with the same prompt
2. **Measure**: Track costs and latency for your use case
3. **Optimize**: Switch to the best provider for your needs
4. **Integrate**: Add to your production app
5. **Monitor**: Track performance over time

## Resources

- 📖 [Provider Documentation](../providers/README.md)
- 🔧 [Model Configurations](../providers/*/models.json)
- 🐛 [Report Issues](https://github.com/justinlietz93/Modular_Utilities/issues)

---

**Happy Prompting! 🚀** Your AI integration just became vendor-agnostic.
