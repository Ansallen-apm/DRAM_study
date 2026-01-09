#!/bin/bash
# Script to run DRAMSys simulations with different trace configurations

BIN=DRAMSys/build/bin/DRAMSys
RESULTS_FILE=trace_results.txt

echo "Trace Type	Burst Size	Bandwidth (GB/s)	Utilization (%)" > $RESULTS_FILE
echo "-----------------------------------------------------------------" >> $RESULTS_FILE

# Run Sequential Traces
for size in 64 128 256; do
    echo "Running Sequential ${size}B..."
    $BIN configs/seq_${size}.json > temp_seq_${size}.log 2>&1
    bw=$(grep "AVG BW" temp_seq_${size}.log | head -n 1 | awk '{print $7}')
    util=$(grep "AVG BW" temp_seq_${size}.log | head -n 1 | awk '{print $10}')
    echo -e "seq\t\t${size}B\t\t${bw}\t\t\t${util}" >> $RESULTS_FILE
    rm temp_seq_${size}.log
done

# Run Random Traces
for size in 64 128 256; do
    echo "Running Random ${size}B..."
    $BIN configs/rand_${size}.json > temp_rand_${size}.log 2>&1
    bw=$(grep "AVG BW" temp_rand_${size}.log | head -n 1 | awk '{print $7}')
    util=$(grep "AVG BW" temp_rand_${size}.log | head -n 1 | awk '{print $10}')
    echo -e "rand\t\t${size}B\t\t${bw}\t\t\t${util}" >> $RESULTS_FILE
    rm temp_rand_${size}.log
done

cat $RESULTS_FILE
