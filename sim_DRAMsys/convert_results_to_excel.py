import pandas as pd
import sys

def convert_to_excel(input_file, output_file):
    try:
        # Read the file, skipping the second line (separator)
        # We assume tab separation based on the input file
        with open(input_file, 'r') as f:
            lines = f.readlines()

        # Filter out the separator line
        data_lines = [line for line in lines if not line.startswith('---')]

        from io import StringIO
        data_str = "".join(data_lines)

        # Parse using pandas
        df = pd.read_csv(StringIO(data_str), sep='\t')

        # Strip whitespace from column names and values
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

        # Save to Excel
        df.to_excel(output_file, index=False)
        print(f"Successfully converted {input_file} to {output_file}")

    except Exception as e:
        print(f"Error converting file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    input_txt = "trace_results.txt"
    output_xlsx = "trace_results.xlsx"
    convert_to_excel(input_txt, output_xlsx)
