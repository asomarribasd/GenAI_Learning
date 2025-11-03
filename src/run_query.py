#!/usr/bin/env python3
"""
Multi-Task Text Utility - Customer Support Assistant
Main query processor that accepts user questions and returns structured JSON responses.
"""

import os
import json
import time
import csv
from datetime import datetime
from pathlib import Path
import argparse
from typing import Dict, Any, Optional

import openai
from dotenv import load_dotenv, dotenv_values
from safety import PromptSafetyChecker, SafetyLevel
from assistant import CustomerSupportAssistant
from metrics_logger import MetricsLogger


# Load environment variables
for key in dotenv_values().keys():
    os.environ.pop(key, None)

load_dotenv(override=True)

def main():
    """Command line interface for the assistant"""
    parser = argparse.ArgumentParser(description='Customer Support Assistant')
    parser.add_argument('question', nargs='?', help='Customer question to process')
    parser.add_argument('--interactive', '-i', action='store_true', help='Start interactive mode')
    parser.add_argument('--output', '-o', help='Output file for JSON response')
    
    args = parser.parse_args()
    
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please copy .env.example to .env and add your API key.")
        return
    
    assistant = CustomerSupportAssistant()
    
    if args.interactive:
        # Interactive mode
        print("Customer Support Assistant (Interactive Mode)")
        print("Type 'quit' or 'exit' to stop\n")
        
        while True:
            try:
                question = input("Customer Question: ").strip()
                if question.lower() in ['quit', 'exit']:
                    break
                
                if not question:
                    continue
                
                print("\nProcessing...")
                result = assistant.process_query(question)
                
                print("\n" + "="*60)
                print("RESPONSE:")
                print(json.dumps(result['response'], indent=2))
                print("\nMETRICS:")
                for key, value in result['metrics'].items():
                    print(f"  {key}: {value}")
                print("="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
    
    elif args.question:
        # Single question mode
        result = assistant.process_query(args.question)
        
        output = {
            'question': args.question,
            'response': result['response'],
            'metrics': result['metrics']
        }
        
        json_output = json.dumps(output, indent=2)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"Response saved to {args.output}")
        else:
            print(json_output)
    
    else:
        # No question provided
        print("Usage: python src/run_query.py \"Your customer question here\"")
        print("Or use: python src/run_query.py --interactive")

if __name__ == "__main__":
    main()