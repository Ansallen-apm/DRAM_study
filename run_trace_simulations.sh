#!/bin/bash
# Script to run DRAMSys simulations with different trace configurations

BIN=DRAMSys/build/bin/DRAMSys
RESULTS_FILE=trace_results.txt
TEMPLATE_DIR=configs/templates
CONFIG_DIR=configs

mkdir -p $CONFIG_DIR

# Header
echo -e "Trace Type\tBurst Size\tRW Ratio\tBandwidth (GB/s)\tUtilization (%)" > $RESULTS_FILE
echo "-------------------------------------------------------------------------------------" >> $RESULTS_FILE

SIZES=(64 128 256)
RATIOS=(1.0 0.5 0.0)

# Function to run simulation
run_sim() {
    type=$1
    size=$2
    ratio=$3

    template="${TEMPLATE_DIR}/${type}_template.json"
    config="${CONFIG_DIR}/${type}_${size}_${ratio}.json"

    # Generate config
    cp $template $config
    sed -i "s/SIZE/${size}/g" $config
    sed -i "s/RWRATIO/${ratio}/g" $config

    echo "Running ${type} ${size}B RW=${ratio}..."

    # Run DRAMSys
    $BIN $config > temp.log 2>&1

    # Extract results
    # Adjust grep/awk based on log format
    # Log format: "AVG BW:         23.92  Gb/s | 2.99   GB/s | 46.73  %"
    # Columns: 1:AVG 2:BW: 3:Gb/s_val 4:Gb/s 5:| 6:GB/s_val 7:GB/s 8:| 9:Util_val 10:%
    # Wait, in previous step I used $7 and $10?
    # "DRAMSys.controller0       AVG BW:         23.92  Gb/s | 2.99   GB/s | 46.73  %"
    # 1:DRAMSys.controller0 2:AVG 3:BW: 4:23.92 5:Gb/s 6:| 7:2.99 8:GB/s 9:| 10:46.73 11:%
    # So $7 is GB/s, $10 is %.

    bw=$(grep "AVG BW" temp.log | head -n 1 | awk '{print $7}')
    util=$(grep "AVG BW" temp.log | head -n 1 | awk '{print $10}')

    echo -e "${type}\t\t${size}B\t\t${ratio}\t\t${bw}\t\t\t${util}" >> $RESULTS_FILE

    rm temp.log
}

# Run Sequential Traces
for size in "${SIZES[@]}"; do
    for ratio in "${RATIOS[@]}"; do
        run_sim "seq" $size $ratio
    done
done

# Run Random Traces
for size in "${SIZES[@]}"; do
    for ratio in "${RATIOS[@]}"; do
        run_sim "rand" $size $ratio
    done
done

cat $RESULTS_FILE
