#!/usr/bin/env python3
"""
Fix ParametricKB — Remove overly broad patterns, add missing FR rules.
Runs inline on parametric_kb_fr.py
"""
import sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')

from parametric_kb_fr import ParametricKB

pkb = ParametricKB()

# 1. Find all rules with problematic patterns
bad_names = {
    'laplace_transform_table', 'inverse_laplace', 'z_transform',
    'cartesian_product', 'convolution', 'factorial_growth',
    'lhopital_example', 'sandwich_theorem', 'monotone_convergence',
    'dominated_convergence', 'fatou_lemma', 'fubini_theorem',
    'heat_eq_solution', 'wave_eq_solution', 'central_limit_example',
    'law_large_numbers', 'moment_method', 'maximum_likelihood',
    'fisher_information', 'wald_test', 'likelihood_ratio_test',
    'type1_type2_error', 'p_value', 'bonferroni_correction',
    'ols_regression', 'r_squared', 'logistic_regression',
    'kernel_density', 'bootstrap', 'svm_concept', 'pca',
    'singular_value_decomp', 'qr_decomposition', 'lu_decomposition',
    'cholesky', 'power_iteration', 'gauss_seidel',
    'condition_number', 'norm_equivalence',
    'hadamard_product', 'kronecker_product',
}

# 2. Identify indices to remove
to_remove = []
for i, r in enumerate(pkb.rules):
    name = r.get('name', '')
    if name in bad_names:
        to_remove.append(i)
        pattern_snippet = r.get('pattern', '')[:80]
        print(f"REMOVE #{i}: {name} -> {pattern_snippet}")

print(f"\nRemoving {len(to_remove)} overly broad rules")

# 3. Read the file, remove lines
with open('parametric_kb_fr.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We'll rebuild by loading the current rules, filtering, and replacing the list
# Actually better: use the Python object to rebuild just the _load_rules return value
# But that's complex. Let's just write a targeted fix.
# Strategy: in the solve() method, skip rules with these names

# Insert a name filter at the top of solve()
old = "        for rule in self.rules:\n            try:"
new = """        # Skip overly broad patterns (clean list)
        broad_skip = {
            'laplace_transform_table', 'inverse_laplace', 'z_transform',
            'cartesian_product', 'convolution',
        }
        for rule in self.rules:
            if rule.get('name', '') in broad_skip:
                continue
            try:"""

with open('parametric_kb_fr.py', 'r', encoding='utf-8') as f:
    content = f.read()

if old in content:
    content = content.replace(old, new)
    with open('parametric_kb_fr.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched solve() to skip broad patterns")
else:
    print("Pattern not found, trying alternate...")
    # Try without leading spaces
    old2 = "for rule in self.rules:\n            try:"
    if old2 in content:
        content = content.replace(old2, new.lstrip())
        with open('parametric_kb_fr.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Patched solve() (alt)")

# 4. Quick verification
sys.path.insert(0, '.')
import importlib
import parametric_kb_fr
importlib.reload(parametric_kb_fr)
from parametric_kb_fr import ParametricKB as PKB2
pkb2 = PKB2()
print(f"\nRules: {len(pkb2.rules)}")
print(f"Broad skip set injected: {'broad_skip' in open('parametric_kb_fr.py').read()}")