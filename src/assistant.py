import os
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import openai
from safety import PromptSafetyChecker, SafetyLevel
from metrics_logger import MetricsLogger

class CustomerSupportAssistant:
    """Main class for processing customer support queries"""
    TOKEN_PRICING = {
        'gpt-5': {'input': 1.25, 'output': 10.00},
        'gpt-5 nano': {'input': 0.05, 'output': 0.40},
    }

    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('DEFAULT_MODEL', 'gpt-5 nano')
        self.max_tokens = int(os.getenv('MAX_TOKENS', '1000'))
        self.temperature = float(os.getenv('TEMPERATURE', '0.7'))
        self.metrics_logger = MetricsLogger()
        self.prompt_template = self._load_prompt_template()
        self.safety_checker = PromptSafetyChecker()

    def _load_prompt_template(self) -> str:
        prompt_file = Path("../prompts/main_prompt.txt")
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        if model not in self.TOKEN_PRICING:
            pricing = self.TOKEN_PRICING['gpt-3.5-turbo']
        else:
            pricing = self.TOKEN_PRICING[model]
        input_cost = (prompt_tokens / 1000) * pricing['input']
        output_cost = (completion_tokens / 1000) * pricing['output']
        return round(input_cost + output_cost, 6)

    def _validate_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                return None
            json_str = response[start_idx:end_idx]
            parsed = json.loads(json_str)
            required_fields = ['answer', 'confidence', 'actions', 'category', 'urgency']
            if not all(field in parsed for field in required_fields):
                return None
            if not isinstance(parsed['answer'], str):
                return None
            if not isinstance(parsed['confidence'], (int, float)) or not (0 <= parsed['confidence'] <= 1):
                return None
            if not isinstance(parsed['actions'], list):
                return None
            if not isinstance(parsed['category'], str):
                return None
            if parsed['urgency'] not in ['low', 'medium', 'high']:
                return None
            return parsed
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def process_query(self, user_question: str) -> Dict[str, Any]:
        start_time = time.time()
        timestamp = datetime.now().isoformat()
        safety_result = self.safety_checker.assess_safety(user_question)
        if safety_result.should_block:
            end_time = time.time()
            latency_ms = round((end_time - start_time) * 1000, 2)
            safety_response = self.safety_checker.get_safe_fallback_response(safety_result)
            safety_metrics = {
                'timestamp': timestamp,
                'tokens_prompt': 0,
                'tokens_completion': 0,
                'total_tokens': 0,
                'latency_ms': latency_ms,
                'estimated_cost_usd': 0.0,
                'model': 'safety_filter',
                'question_preview': f"BLOCKED: {user_question[:40]}..."
            }
            self.metrics_logger.log_metrics(safety_metrics)
            return {
                'response': safety_response,
                'metrics': safety_metrics,
                'safety_result': {
                    'level': safety_result.level.value,
                    'reasons': safety_result.reasons,
                    'confidence': safety_result.confidence
                }
            }
        query_to_process = safety_result.modified_input or user_question
        prompt = self.prompt_template.format(user_question=query_to_process)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            end_time = time.time()
            latency_ms = round((end_time - start_time) * 1000, 2)
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            estimated_cost = self._estimate_cost(prompt_tokens, completion_tokens, self.model)
            assistant_response = response.choices[0].message.content
            parsed_response = self._validate_json_response(assistant_response)
            if parsed_response is None:
                parsed_response = {
                    "answer": "I apologize, but I encountered an error processing your request. Please contact our support team directly for assistance.",
                    "confidence": 0.1,
                    "actions": [
                        "Escalate to human support agent",
                        "Log the parsing error for technical review"
                    ],
                    "category": "system_error",
                    "urgency": "medium"
                }
            metrics = {
                'timestamp': timestamp,
                'tokens_prompt': prompt_tokens,
                'tokens_completion': completion_tokens,
                'total_tokens': total_tokens,
                'latency_ms': latency_ms,
                'estimated_cost_usd': estimated_cost,
                'model': self.model,
                'question_preview': user_question[:50] + "..." if len(user_question) > 50 else user_question
            }
            self.metrics_logger.log_metrics(metrics)
            return {
                'response': parsed_response,
                'metrics': metrics,
                'raw_response': assistant_response
            }
        except Exception as e:
            end_time = time.time()
            latency_ms = round((end_time - start_time) * 1000, 2)
            error_response = {
                "answer": f"I encountered a technical error: {str(e)}. Please try again or contact support.",
                "confidence": 0.0,
                "actions": [
                    "Check API connection and retry",
                    "Escalate to technical support if error persists"
                ],
                "category": "technical_error",
                "urgency": "high"
            }
            error_metrics = {
                'timestamp': timestamp,
                'tokens_prompt': 0,
                'tokens_completion': 0,
                'total_tokens': 0,
                'latency_ms': latency_ms,
                'estimated_cost_usd': 0.0,
                'model': self.model,
                'question_preview': f"ERROR: {user_question[:40]}..."
            }
            self.metrics_logger.log_metrics(error_metrics)
            return {
                'response': error_response,
                'metrics': error_metrics,
                'error': str(e)
            }
