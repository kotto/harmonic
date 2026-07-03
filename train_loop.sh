#!/bin/bash
# Relance l'entrainement toutes les 2 heures
# Usage: bash train_loop.sh

ENGINE_DIR="E:/SAAS - Copie/engine"
MAX_TIME=110  # minutes (un peu moins de 2h pour marge)
TOTAL_CYCLES=6  # 6 x 2h = 12h total

echo "============================================"
echo "HARMONIC TRAINING LOOP"
echo "  Cycles: $TOTAL_CYCLES x ${MAX_TIME}min"
echo "  Started at: $(date)"
echo "============================================"

for i in $(seq 1 $TOTAL_CYCLES); do
    echo ""
    echo "=== CYCLE $i/$TOTAL_CYCLES — $(date) ==="
    
    cd "$ENGINE_DIR"
    python train_continue.py \
        --steps 99999 \
        --batch_size 2 \
        --seq_len 64 \
        --save_every 50 \
        --max_time $MAX_TIME \
        --skip_calibration
    
    RC=$?
    echo "  Exit code: $RC"
    
    # Sauvegarder les stats du cycle
    echo "Cycle $i: $(date) - exit=$RC" >> "$ENGINE_DIR/../data/training_output/training_cycles.log"
    
    if [ $i -lt $TOTAL_CYCLES ]; then
        echo "  Sleeping 30s before next cycle..."
        sleep 30
    fi
done

echo ""
echo "============================================"
echo "TRAINING LOOP COMPLETE — $(date)"
echo "============================================"
