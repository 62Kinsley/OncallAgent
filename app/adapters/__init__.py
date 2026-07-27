"""Investigation adapters: mock/real data sources and Slack notifications."""
from .logs import query_logs
from .metrics import query_metrics
from .slack import post_slack_summary

__all__ = ["query_logs", "query_metrics", "post_slack_summary"]
