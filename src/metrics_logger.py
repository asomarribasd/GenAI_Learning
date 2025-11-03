import csv
from pathlib import Path
from typing import Dict, Any

class MetricsLogger:
    """Handles logging of per-query metrics"""
    def __init__(self, metrics_file: str = "metrics/metrics.csv"):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(exist_ok=True)
        self._ensure_csv_headers()

    def _ensure_csv_headers(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.metrics_file.exists():
            with open(self.metrics_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 
                    'tokens_prompt', 
                    'tokens_completion', 
                    'total_tokens', 
                    'latency_ms', 
                    'estimated_cost_usd',
                    'model',
                    'question_preview'
                ])

    def log_metrics(self, metrics: Dict[str, Any]):
        """Log metrics to CSV file"""
        with open(self.metrics_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                metrics['timestamp'],
                metrics['tokens_prompt'],
                metrics['tokens_completion'],
                metrics['total_tokens'],
                metrics['latency_ms'],
                metrics['estimated_cost_usd'],
                metrics['model'],
                metrics['question_preview']
            ])