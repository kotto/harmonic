# Makefile pour HCV Decoder Standalone
# Phase 1 - Terminé

CC = gcc
CFLAGS = -O3 -march=native -Wall -Wextra -fPIC
LDFLAGS = -shared

# Cible par défaut
all: libhcvdecoder.so test_hcv_decoder

# Bibliothèque partagée
libhcvdecoder.so: hcv_decoder.o
	$(CC) $(LDFLAGS) -o $@ $^

hcv_decoder.o: hcv_decoder.c hcv_decoder.h
	$(CC) $(CFLAGS) -c $< -o $@

# Test unitaire
test_hcv_decoder: test_hcv_decoder.o libhcvdecoder.so
	$(CC) -o $@ test_hcv_decoder.o -L. -lhcvdecoder

test_hcv_decoder.o: test_hcv_decoder.c hcv_decoder.h
	$(CC) $(CFLAGS) -c $< -o $@

# Exécuter les tests
test: test_hcv_decoder
	LD_LIBRARY_PATH=. ./test_hcv_decoder

# Nettoyage
clean:
	rm -f *.o *.so test_hcv_decoder

.PHONY: all test clean
