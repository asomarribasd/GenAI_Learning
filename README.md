# GenAI_Learning - Customer Support Assistant

A Python script that provides structured JSON responses for customer support queries using OpenAI's API. The system includes comprehensive metrics tracking, safety moderation, and automated testing.

## Features

- **Structured JSON Responses**: Returns consistent JSON format with answer, confidence, actions, category, and urgency
- **Comprehensive Metrics**: Tracks tokens, latency, and estimated costs for each query
- **Advanced Prompt Engineering**: Uses instruction-based templates with few-shot examples
- **Safety Moderation**: Detects and blocks adversarial prompts and inappropriate content
- **Automated Testing**: Includes unit tests for JSON validation and core functionality
- **Interactive and CLI Modes**: Supports both single queries and interactive sessions

## Project Structure

```
GenAI_Learning/
├── src/
│   ├── run_query.py      # Main application script
│   └── safety.py         # Safety and moderation module
├── prompts/
│   └── main_prompt.txt   # Prompt engineering template
├── metrics/
│   ├── metrics.csv       # Per-query metrics (auto-generated)
│   └── safety_log.txt    # Safety decisions log (auto-generated)
├── tests/
│   └── test_core.py      # Automated test suite
├── reports/
│   └── PI_report_en.md   # Technical report
├── pyproject.toml       # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Poetry ([Install Poetry](https://python-poetry.org/docs/#installation))
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Setup Steps

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd GenAI_Learning
   ```

2. **Install dependencies with Poetry**
   ```bash
   poetry install
   ```

3. **Configure environment variables**
   ```bash
   # Copy the example environment file
   copy .env.example .env
   
   # Edit .env and add your OpenAI API key
   # OPENAI_API_KEY=your_actual_api_key_here
   ```

4. **Verify installation**
   ```bash
   poetry run python tests/test_core.py
   ```

## Usage

### Command Line Interface

**Single Query:**
```bash
poetry run python src/run_query.py "I can't log into my account"
```

**Save output to file:**
```bash
poetry run python src/run_query.py "Where is my order?" --output response.json
```

**Interactive Mode:**
```bash
poetry run python src/run_query.py --interactive
```

**Alternative using Poetry scripts:**
```bash
poetry run run-query "I can't log into my account"
poetry run run-query --interactive
```

### Example Output

```json
{
  "question": "I can't log into my account",
  "response": {
    "answer": "This appears to be a login authentication issue. Please try resetting your password using the 'Forgot Password' link. If the issue persists, your account may be temporarily locked for security reasons.",
    "confidence": 0.85,
    "actions": [
      "Guide customer through password reset process",
      "Check if account is locked in admin panel",
      "Verify customer identity before unlocking account"
    ],
    "category": "authentication",
    "urgency": "medium"
  },
  "metrics": {
    "timestamp": "2024-01-01T12:00:00.000000",
    "tokens_prompt": 245,
    "tokens_completion": 67,
    "total_tokens": 312,
    "latency_ms": 1250.5,
    "estimated_cost_usd": 0.000468,
    "model": "gpt-4-nano"
  }
}
```

## Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | - |
| `DEFAULT_MODEL` | OpenAI model to use | `gpt-4-nano` |
| `MAX_TOKENS` | Maximum tokens in response | `1000` |
| `TEMPERATURE` | Response creativity (0.0-1.0) | `0.7` |

## Safety Features

The system includes advanced safety moderation that:

- **Detects Prompt Injection**: Identifies attempts to override system instructions
- **Content Filtering**: Blocks inappropriate or harmful content
- **Input Sanitization**: Cleans potentially problematic input
- **Fallback Responses**: Provides safe responses for blocked content
- **Comprehensive Logging**: Records all safety decisions for analysis

### Testing Safety

```bash
poetry run python src/safety.py
# or
poetry run test-safety
```

This runs tests against various adversarial prompts to demonstrate the safety system.

## Metrics and Monitoring

### Metrics Tracked

All queries generate metrics automatically saved to `metrics/metrics.csv`:

- **Timestamp**: When the query was processed
- **Token Usage**: Prompt, completion, and total tokens
- **Latency**: Response time in milliseconds
- **Cost**: Estimated USD cost based on current OpenAI pricing
- **Model**: Which AI model was used
- **Question Preview**: First 50 characters of the query

### Viewing Metrics

```bash
# View recent metrics
tail -10 metrics/metrics.csv

# Open in Excel or similar for analysis
start metrics/metrics.csv
```

## Testing

### Run All Tests

```bash
poetry run python tests/test_core.py
# or
poetry run pytest
```

### Test Categories

- **JSON Validation**: Ensures responses conform to required schema
- **Token Counting**: Validates cost calculations and token usage
- **Safety Testing**: Verifies adversarial prompt detection
- **Error Handling**: Tests API failures and edge cases

## Prompt Engineering Techniques

The system implements several advanced prompt engineering techniques:

1. **Instruction-Based Template**: Clear, structured instructions for the AI
2. **Few-Shot Learning**: Provides 3 examples of ideal responses
3. **JSON Schema Enforcement**: Explicit format requirements
4. **Chain-of-Thought**: Guides the AI through reasoning steps
5. **Response Validation**: Post-processing to ensure quality

## Cost Optimization

- **Efficient Prompts**: Optimized template to minimize token usage
- **Model Selection**: Defaults to cost-effective GPT-3.5-turbo
- **Token Limits**: Configurable maximum response length
- **Cost Tracking**: Real-time cost monitoring per query

## Troubleshooting

### Common Issues

**"API key not found" error:**
```bash
# Verify your .env file exists and contains:
OPENAI_API_KEY=your_actual_key_here
```

**"Prompt template not found" error:**
```bash
# Ensure the prompts directory exists:
mkdir prompts
# Make sure main_prompt.txt is in the prompts folder
```

**Import errors:**
```bash
# Install missing dependencies:
poetry install
```

**Permission errors on Windows:**
```bash
# Run PowerShell as Administrator if needed
```

### Debug Mode

For debugging, you can modify the environment variables:

```bash
# In .env file, add:
DEBUG=true
VERBOSE_LOGGING=true
```

## Performance

**Typical Performance Metrics:**
- **Latency**: 800-2000ms depending on model and query complexity
- **Cost**: $0.0003-0.002 per query with GPT-3.5-turbo
- **Accuracy**: 85-95% confidence for well-formed customer support queries

## Known Limitations

1. **API Dependency**: Requires internet connection and OpenAI API access
2. **Cost Accumulation**: Each query incurs a small cost
3. **Rate Limits**: Subject to OpenAI API rate limits
4. **Language**: Optimized for English customer support queries
5. **Context**: No conversation history between queries

## Contributing

To extend the system:

1. **Add new prompt techniques**: Modify `prompts/main_prompt.txt`
2. **Enhance safety**: Update patterns in `src/safety.py`
3. **Add tests**: Extend `tests/test_core.py`
4. **New metrics**: Modify `MetricsLogger` in `src/run_query.py`

## License

This project is for educational and demonstration purposes. Please ensure compliance with OpenAI's usage policies when deploying.

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the test output for specific errors
3. Ensure all environment variables are correctly set
4. Verify your OpenAI API key has sufficient credits
Generative AI learning samples.

First Commit
