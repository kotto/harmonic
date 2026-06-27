#!/bin/bash
cd /opt/connective-ai
grep -n "combined_content" PARALLEL_MULTI_MODAL_AGGREGATION.py || echo "Not found"
grep -n "aggregate_parallel_responses" PARALLEL_MULTI_MODAL_AGGREGATION.py | head -5
