#!/bin/bash
cd /opt/connective-ai
python3 -c "
from harmonic_response_generator_simple import HarmonicResponseGenerator
h = HarmonicResponseGenerator()
result = h.generate_response('test')
print('CONTENT LENGTH:', len(result['content']))
print('FIRST 100 CHARS:', result['content'][:100])
print('DETERMINISM:', result['determinism_level'])
"
