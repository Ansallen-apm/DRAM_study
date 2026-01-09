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

# Convert to Excel
if command -v python3 &> /dev/null; then
    echo "Converting results to Excel..."
    python3 convert_results_to_excel.py
fi
