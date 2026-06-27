#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from holographic_ensemble import HolographicEnsemble

ensemble = HolographicEnsemble()
ensemble.build_all(force_rebuild=False)
result = ensemble.ingest_quickfacts()
print('\n=== INGESTION TERMINEE ===')
print(result)
ensemble.audit_all()