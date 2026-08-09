# Problem: Extracting Structured Operations from Math Word Problems

## Task

Given a math word problem in natural language, extract a sequence of structured operations that can be executed to compute the answer.

**Input example:**
```
"John has 5 apples. Mary has 3 times as many. How many apples does Mary have?"
```

**Expected output (structured operations):**
```
INIT(entity="john", object="apples", value=5)
MULTIPLY(entity="mary", object="apples", multiplier=3, reference_entity="john")
QUERY(entity="mary", object="apples") → 15
```

## What We Have

### 1. A working arithmetic engine
The backend can execute structured operations and produce correct answers. It handles chained operations, cross-references between entities, and algebraic dependencies (e.g., `mary.apples = john.apples × 3`). This component is verified and stable — given correct structured input, it always produces the correct output.

### 2. Training data
1101 annotated math word problems (GSM8K training split), each with a chain-of-thought answer containing explicit operation annotations:

```
Problem: "Janet's ducks lay 16 eggs per day. She eats 3 for breakfast and bakes 4 for friends. She sells the remainder at $2 each. How much does she make?"
Answer: "... 16 - 3 - 4 = <<16-3-4=9>>9 eggs. She makes 9 * 2 = $<<9*2=18>>18 per day. #### 18"
```

Each `<<a op b = c>>` annotation reveals the exact operation sequence. We can align these operations with the problem sentences that triggered them, yielding ~4000 labeled (sentence → operation) pairs.

### 3. Operation types to extract
From the problem text, we need to identify for each sentence:

| Operation | Example sentence | Parameters needed |
|-----------|-----------------|-------------------|
| INIT | "John has 5 apples." | entity, object, value |
| ADD | "He buys 3 more." | entity, value (object = last_object) |
| SUBTRACT | "She ate 4." | entity, value (object = last_object) |
| MULTIPLY | "Mary has 3 times as many." | entity, multiplier, reference_entity |
| CROSS_MULT | "Each box has 5 pencils." | container_count, per_unit, product |
| RATE | "James earns $20 per hour." | entity, rate |
| DIVIDE | "Split into 4 equal groups." | value, divisor |

## What We've Tried

All approaches perform at **100% on 15 hand-picked simple examples** but drop to **~2-3% on 200 randomly sampled real GSM8K problems**. The gap reveals that simple examples are not representative.

| Approach | Accuracy (200 real problems) | Notes |
|----------|------------------------------|-------|
| Hand-crafted regex rules (15 rules) | 1.0% | Fragile, doesn't generalize |
| Data-mined regex rules (721 rules) | 2.5% | Better coverage but over-normalized |
| k-NN retrieval (cosine similarity on embeddings) | 0.5% | Surface similarity ≠ structural similarity |
| Logistic regression on sentence embeddings (MiniLM, 384-dim) | 2.5% | Good at operation type detection (58%), but parameter extraction still heuristic |
| T5-small fine-tuned (LoRA, 344K trainable) | 3.6% | Generates plausible but mathematically wrong operations (e.g., "5 × 3 = 20") |

## Root Cause: Parameter Extraction

**Operation type detection is not the main bottleneck.** A classifier trained on 4000 examples achieves 58% accuracy at identifying the correct operation type for a sentence.

**The bottleneck is extracting the correct parameters** (entity, object, value) and mapping them to their roles in the operation. Current heuristics:

- **Entity detection**: find the first capitalized word → works for "John", "Mary", fails for "A bakery", "There are 6 boxes"
- **Object detection**: find the last noun before a number → works for "has 5 apples", fails for "each box has 5 pencils" (returns "box" instead of "pencils")
- **Value extraction**: take the first number → works for simple values, fails when numbers play different roles (3 in "3 times" is a multiplier, not a value)
- **Coreference**: reuse the last entity → works for adjacent sentences, fails across 3+ sentence chains and for impersonal referents ("They sell..." → who is "they"?)

These heuristics cover the 15 simple examples perfectly but break on real problems where entities are implicit, objects shift between sentences, and numbers have context-dependent semantics.

## Constraints

1. **Lightweight**: the extraction module should be efficient (< 100ms per problem). The arithmetic engine handles complex computation; the NLP is a compiler, not a reasoner.

2. **Modular**: the extraction module is an interchangeable front-end. It outputs structured operations consumed by the arithmetic back-end.

3. **Training data**: we have 1101 problems with ~4000 annotated (sentence → operation) pairs. No external APIs or massive pre-trained models required, though small models (MiniLM, T5-small) are available.

4. **Output format**: the extraction must produce structured operations with explicit entity, object, and value parameters — not just a final numeric answer. The arithmetic back-end needs to track state across multiple sentences.

## Question

How can we build a robust parameter extractor for math word problems that maps each sentence to `(operation_type, entity, object, value, role)` with sufficient accuracy to significantly exceed the current ~3% ceiling on real GSM8K problems?

Specifically: given a sentence like "Each box has 5 pencils" preceded by "There are 6 boxes", how do we extract that:
- The operation is CROSS_MULT (multiply container count by per-unit quantity)
- The container is "boxes" (count = 6, from previous sentence)
- The per-unit quantity is 5
- The product is "pencils"
- The result should be stored as `total_pencils = 6 × 5`

And for "Mary has 3 times as many apples as John", how do we extract:
- The operation is MULTIPLY
- The entity is "Mary"
- The object is "apples" (implicit from context)
- The multiplier is 3
- The reference entity is "John" (connected via "as many as", not directly present in the sentence)

## Key Files

- `engine/compilateur_thu.py` — current compiler (grammar rules + MiniLM classifier + execution)
- `engine/train_minilm_operations.py` — training script for operation type classifier
- `engine/extraire_grammaire.py` — grammar rule mining from training data
- `engine/data/benchmarks/gsm8k_test.jsonl` — 1319 annotated problems
- `engine/raisonneur_ondulatoire.py` — arithmetic back-end (entity/object tracking + algebraic solver)
