#!/usr/bin/env bash
# Seed a few custom CloudWatch metrics for OncallAgent demos.
# Cost: a handful of PutMetricData calls (very small).
set -euo pipefail

REGION="${AWS_REGION:-us-west-2}"
NAMESPACE="${CW_METRICS_NAMESPACE:-OncallAgent/Demo}"
SERVICE="${1:-checkout-api}"

echo "Seeding metrics:"
echo "  region=$REGION"
echo "  namespace=$NAMESPACE"
echo "  service=$SERVICE"

aws cloudwatch put-metric-data \
  --region "$REGION" \
  --namespace "$NAMESPACE" \
  --metric-data "[
    {
      \"MetricName\": \"ErrorRatePct\",
      \"Dimensions\": [{\"Name\": \"ServiceName\", \"Value\": \"$SERVICE\"}],
      \"Value\": 12.0,
      \"Unit\": \"Percent\"
    },
    {
      \"MetricName\": \"LatencyP95Ms\",
      \"Dimensions\": [{\"Name\": \"ServiceName\", \"Value\": \"$SERVICE\"}],
      \"Value\": 3400.0,
      \"Unit\": \"Milliseconds\"
    },
    {
      \"MetricName\": \"CpuUsagePct\",
      \"Dimensions\": [{\"Name\": \"ServiceName\", \"Value\": \"$SERVICE\"}],
      \"Value\": 91.0,
      \"Unit\": \"Percent\"
    }
  ]"

echo "Done. Wait ~30-60s, then query with:"
echo "  aws cloudwatch get-metric-data --region $REGION ..."
echo "Or set USE_MOCK_ADAPTERS=false and run: python app/main.py"
