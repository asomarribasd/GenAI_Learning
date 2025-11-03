#!/usr/bin/env python3
"""
Test suite for the Customer Support Assistant
Tests JSON validation, token counting, and core functionality.
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from run_query import CustomerSupportAssistant, MetricsLogger

class TestMetricsLogger(unittest.TestCase):
    """Test the MetricsLogger functionality"""
    
    def setUp(self):
        self.test_metrics_file = "metrics/test_metrics.csv"
        # Clean up any existing test file
        if os.path.exists(self.test_metrics_file):
            os.remove(self.test_metrics_file)
    
    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.test_metrics_file):
            os.remove(self.test_metrics_file)
    
    def test_metrics_logger_creation(self):
        """Test that MetricsLogger creates CSV with proper headers"""
        logger = MetricsLogger(self.test_metrics_file)
        
        self.assertTrue(os.path.exists(self.test_metrics_file))
        
        # Check headers
        with open(self.test_metrics_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            expected_headers = "timestamp,tokens_prompt,tokens_completion,total_tokens,latency_ms,estimated_cost_usd,model,question_preview"
            self.assertEqual(first_line, expected_headers)
    
    def test_metrics_logging(self):
        """Test that metrics are logged correctly"""
        logger = MetricsLogger(self.test_metrics_file)
        
        test_metrics = {
            'timestamp': '2024-01-01T12:00:00',
            'tokens_prompt': 100,
            'tokens_completion': 50,
            'total_tokens': 150,
            'latency_ms': 500.0,
            'estimated_cost_usd': 0.001,
            'model': 'gpt-3.5-turbo',
            'question_preview': 'Test question...'
        }
        
        logger.log_metrics(test_metrics)
        
        # Verify the data was logged
        with open(self.test_metrics_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)  # Header + 1 data row
            data_line = lines[1].strip()
            self.assertIn('2024-01-01T12:00:00', data_line)
            self.assertIn('100', data_line)
            self.assertIn('50', data_line)
            self.assertIn('150', data_line)

class TestCustomerSupportAssistant(unittest.TestCase):
    """Test the main CustomerSupportAssistant functionality"""
    
    def setUp(self):
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key',
            'DEFAULT_MODEL': 'gpt-4-nano',
            'MAX_TOKENS': '1000',
            'TEMPERATURE': '0.7'
        })
        self.env_patcher.start()
        
        # Create a test prompt file
        os.makedirs("prompts", exist_ok=True)
        with open("prompts/main_prompt.txt", "w", encoding="utf-8") as f:
            f.write("Test prompt template with {user_question}")
    
    def tearDown(self):
        self.env_patcher.stop()
        # Clean up test files
        if os.path.exists("prompts/main_prompt.txt"):
            os.remove("prompts/main_prompt.txt")
    
    def test_cost_estimation(self):
        """Test token cost estimation"""
        with patch('openai.OpenAI'):
            assistant = CustomerSupportAssistant()
            
            # Test GPT-3.5-turbo pricing
            cost = assistant._estimate_cost(100, 50, 'gpt-3.5-turbo')
            expected_cost = (100/1000 * 0.0015) + (50/1000 * 0.002)
            self.assertAlmostEqual(cost, expected_cost, places=6)
            
            # Test unknown model (should use default pricing)
            cost_unknown = assistant._estimate_cost(100, 50, 'unknown-model')
            self.assertAlmostEqual(cost_unknown, expected_cost, places=6)
    
    def test_json_validation_valid(self):
        """Test JSON response validation with valid input"""
        with patch('openai.OpenAI'):
            assistant = CustomerSupportAssistant()
            
            valid_json = """
            {
                "answer": "This is a test answer",
                "confidence": 0.85,
                "actions": ["action1", "action2"],
                "category": "test",
                "urgency": "medium"
            }
            """
            
            result = assistant._validate_json_response(valid_json)
            self.assertIsNotNone(result)
            self.assertEqual(result['answer'], "This is a test answer")
            self.assertEqual(result['confidence'], 0.85)
            self.assertEqual(result['urgency'], "medium")
    
    def test_json_validation_invalid(self):
        """Test JSON response validation with invalid input"""
        with patch('openai.OpenAI'):
            assistant = CustomerSupportAssistant()
            
            # Test invalid JSON
            invalid_json = "Not a JSON response"
            result = assistant._validate_json_response(invalid_json)
            self.assertIsNone(result)
            
            # Test missing required fields
            incomplete_json = '{"answer": "test"}'
            result = assistant._validate_json_response(incomplete_json)
            self.assertIsNone(result)
            
            # Test invalid confidence value
            invalid_confidence = '''
            {
                "answer": "test",
                "confidence": 1.5,
                "actions": [],
                "category": "test",
                "urgency": "medium"
            }
            '''
            result = assistant._validate_json_response(invalid_confidence)
            self.assertIsNone(result)
            
            # Test invalid urgency value
            invalid_urgency = '''
            {
                "answer": "test",
                "confidence": 0.5,
                "actions": [],
                "category": "test",
                "urgency": "invalid"
            }
            '''
            result = assistant._validate_json_response(invalid_urgency)
            self.assertIsNone(result)
    
    @patch('openai.OpenAI')
    def test_process_query_success(self, mock_openai):
        """Test successful query processing"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "answer": "Test answer",
            "confidence": 0.9,
            "actions": ["test action"],
            "category": "test",
            "urgency": "low"
        }
        '''
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_response.usage.total_tokens = 150
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        assistant = CustomerSupportAssistant()
        result = assistant.process_query("Test question")
        
        # Verify response structure
        self.assertIn('response', result)
        self.assertIn('metrics', result)
        self.assertIn('raw_response', result)
        
        # Verify response content
        response = result['response']
        self.assertEqual(response['answer'], "Test answer")
        self.assertEqual(response['confidence'], 0.9)
        self.assertEqual(response['urgency'], "low")
        
        # Verify metrics
        metrics = result['metrics']
        self.assertEqual(metrics['tokens_prompt'], 100)
        self.assertEqual(metrics['tokens_completion'], 50)
        self.assertEqual(metrics['total_tokens'], 150)
        self.assertGreater(metrics['latency_ms'], 0)
        self.assertGreater(metrics['estimated_cost_usd'], 0)
    
    @patch('openai.OpenAI')
    def test_process_query_api_error(self, mock_openai):
        """Test query processing with API error"""
        # Mock API error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        assistant = CustomerSupportAssistant()
        result = assistant.process_query("Test question")
        
        # Verify error handling
        self.assertIn('response', result)
        self.assertIn('error', result)
        
        response = result['response']
        self.assertEqual(response['category'], "technical_error")
        self.assertEqual(response['urgency'], "high")
        self.assertEqual(response['confidence'], 0.0)

class TestTokenCounting(unittest.TestCase):
    """Test token counting functionality"""
    
    def test_token_calculation_logic(self):
        """Test that token calculations are logical"""
        with patch('openai.OpenAI'):
            assistant = CustomerSupportAssistant()
            
            # Test that longer prompts should generally cost more
            cost_small = assistant._estimate_cost(10, 5, 'gpt-3.5-turbo')
            cost_large = assistant._estimate_cost(1000, 500, 'gpt-3.5-turbo')
            
            self.assertLess(cost_small, cost_large)
            
            # Test that costs are reasonable (not negative, not absurdly high)
            self.assertGreater(cost_small, 0)
            self.assertLess(cost_large, 1.0)  # Should be less than $1 for reasonable usage

class TestJSONSchemaValidation(unittest.TestCase):
    """Test JSON schema validation specifically"""
    
    def test_required_fields_present(self):
        """Test that all required fields are validated"""
        with patch('openai.OpenAI'):
            assistant = CustomerSupportAssistant()
            
            # Test with all required fields
            complete_json = '''
            {
                "answer": "Complete answer",
                "confidence": 0.75,
                "actions": ["action1", "action2", "action3"],
                "category": "general",
                "urgency": "medium"
            }
            '''
            
            result = assistant._validate_json_response(complete_json)
            self.assertIsNotNone(result)
            
            # Test each required field individually
            required_fields = ['answer', 'confidence', 'actions', 'category', 'urgency']
            base_json = json.loads(complete_json)
            
            for field in required_fields:
                test_json = base_json.copy()
                del test_json[field]
                result = assistant._validate_json_response(json.dumps(test_json))
                self.assertIsNone(result, f"Validation should fail when {field} is missing")
    
    def test_data_type_validation(self):
        """Test that data types are properly validated"""
        with patch('openai.OpenAI'):
            assistant = CustomerSupportAssistant()
            
            base_json = {
                "answer": "Test answer",
                "confidence": 0.8,
                "actions": ["action1"],
                "category": "test",
                "urgency": "medium"
            }
            
            # Test invalid answer type (not string)
            invalid_json = base_json.copy()
            invalid_json['answer'] = 123
            result = assistant._validate_json_response(json.dumps(invalid_json))
            self.assertIsNone(result)
            
            # Test invalid actions type (not list)
            invalid_json = base_json.copy()
            invalid_json['actions'] = "not a list"
            result = assistant._validate_json_response(json.dumps(invalid_json))
            self.assertIsNone(result)

def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMetricsLogger,
        TestCustomerSupportAssistant,
        TestTokenCounting,
        TestJSONSchemaValidation
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    print("Running Customer Support Assistant Tests")
    print("=" * 50)
    
    result = run_tests()
    
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)