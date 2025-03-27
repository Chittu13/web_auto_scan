#!/bin/bash

# Check if scanner executable exists
if [[ ! -f "./scanner" ]]; then
    echo "scanner.cpp not compiled. Compiling now..."
    g++ -o scanner scanner.cpp # Compile scanner.cpp
fi

# Run the scanner executable
echo "Running scanner..."
./scanner
