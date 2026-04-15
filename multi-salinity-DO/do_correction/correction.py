
import pandas as pd
import numpy as np
import datetime
import os
import re

# Column name mapping: various possible names -> standard names used by the processor
COLUMN_MAPPING = {
    'unix timestamp': 'Time (sec)',
    'unix_timestamp': 'Time (sec)',
    'time (sec)': 'Time (sec)',
    'time(sec)': 'Time (sec)',
    'temperature': 'T (deg C)',
    't (deg c)': 'T (deg C)',
    'dissolved oxygen': 'DO (mg/l)',
    'do (mg/l)': 'DO (mg/l)',
    'do(mg/l)': 'DO (mg/l)',
}

def detect_do_file_format(file_path):
    """Auto-detect header row, separator, decimal char, and units row in a miniDOT file."""
    header_keywords = ['unix timestamp', 'time (sec)', 'temperature', 'dissolved oxygen']

    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Find the header row: must match at least 2 keywords and contain a delimiter
    header_row = None
    for i, line in enumerate(lines):
        lower_line = line.lower().strip()
        matches = sum(1 for kw in header_keywords if kw in lower_line)
        has_delimiter = ';' in line or line.count(',') >= 2
        if matches >= 2 and has_delimiter:
            header_row = i
            break

    if header_row is None:
        raise ValueError(f"Could not detect column header row in {file_path}. "
                         "Expected columns like 'Unix Timestamp', 'Time (sec)', 'Temperature', or 'Dissolved Oxygen'.")

    # Detect separator
    header_line = lines[header_row]
    sep = ';' if header_line.count(';') > header_line.count(',') else ','

    # Check if the row after header is a units row (contains parenthesized units like "(Second)", "(deg C)")
    skip_units = False
    if header_row + 1 < len(lines):
        next_line = lines[header_row + 1].strip()
        parts = [p.strip() for p in next_line.split(sep) if p.strip()]
        if parts and all(re.match(r'^\(.*\)$', p) for p in parts):
            skip_units = True

    # Detect decimal character from first data row
    decimal = '.'
    data_start = header_row + 1 + (1 if skip_units else 0)
    if data_start < len(lines):
        data_parts = lines[data_start].split(sep)
        for part in data_parts:
            part = part.strip()
            # European decimal: has comma, no period, and looks numeric
            if ',' in part and '.' not in part:
                try:
                    float(part.replace(',', '.', 1))
                    decimal = ','
                    break
                except ValueError:
                    pass

    # Build list of rows to skip: everything before header + units row if present
    skiprows = list(range(header_row))
    if skip_units:
        skiprows.append(header_row + 1)

    return skiprows, sep, decimal

def normalize_do_columns(df):
    """Map various miniDOT column names to the standard names expected by the processor."""
    rename_map = {}
    for col in df.columns:
        clean = col.strip().lower()
        if clean in COLUMN_MAPPING:
            rename_map[col] = COLUMN_MAPPING[clean]
    df.rename(columns=rename_map, inplace=True)
    return df

def DOConcMg(T, P, S):
    return DOConcUmol(T, P, S) * 31.9988 / 1000.0

def DOConcUmol(T, P, S):
    Ptotal = P / 101325.0
    pWSat = SaturatedWaterVaporPressure(T, S)
    pO2measured = pO2(Ptotal - pWSat)
    pO2reference = pO2(1.0 - pWSat)
    return CoStar(T, S) * pO2measured / pO2reference

def SaturatedWaterVaporPressure(T, S):
    TK = T + 273.15
    return np.exp(24.4543 - 67.4509 * 100.0 / TK - 4.8489 * np.log(TK / 100.0) - 5.44E-4 * S)

def CoStar(T, S):
    A = [2.00907, 3.22014, 4.0501, 4.94457, -0.256847, 3.88767]
    B = [-0.00624523, -0.00737614, -0.010341, -0.00817083]
    C0 = -4.88682E-7
    Ts = np.log((298.15 - T) / (273.15 + T))
    CoStar = np.exp(A[0] + A[1] * Ts + A[2] * Ts**2 + A[3] * Ts**3 + A[4] * Ts**4 + A[5] * Ts**5 +
                   S * (B[0] + B[1] * Ts + B[2] * Ts**2 + B[3] * Ts**3) + C0 * S**2)
    CoStar *= 44.6596044945426
    return CoStar

def pO2(P):
    return 0.209446 * P

def SalinityFactor(T, S):
    if S != 0.0:
        return DOConcMg(T, 101325.0, S) / DOConcMg(T, 101325.0, 0.0)
    return 1.0

def elevation_to_pressure(elevation):
    return 101325 * np.exp(-elevation / 8434.5)

def find_closest_salinity(timestamp, salinity_data):
    ts = datetime.datetime.utcfromtimestamp(timestamp)
    time_diff = salinity_data['Timestamp'] - ts
    closest = salinity_data.iloc[(time_diff.abs().argsort()[:1])]
    return closest['Salinity'].values[0]

def save_to_csv(data, output_file_path):
    try:
        data.to_csv(output_file_path, index=False)
        print(f"Data successfully saved to {output_file_path}")
    except Exception as e:
        print(f"Failed to save data: {str(e)}")

class DODataProcessor:
    def __init__(self, pressure):
        self.pressure = pressure

    def calculate_corrected_DO(self, row):
        temperature = row['T (deg C)']
        do_measurement = row['DO (mg/l)']
        sal = row['Salinity']
        salinity = round(sal,2)
        corrected_do = do_measurement * SalinityFactor(temperature, salinity)
        return corrected_do, salinity  # Return unrounded values for flexibility

    def calculate_DO_saturation(self, row):
        temperature = row['T (deg C)']
        do_measurement = row['DO (mg/l)']
        sal = row['Salinity']
        salinity = round(sal,2)
        compensated_do = do_measurement * SalinityFactor(temperature, salinity)
        max_concentration = DOConcMg(temperature, self.pressure, salinity)
        saturation = (compensated_do / max_concentration) * 100
        return saturation
    
def process_all_files(directory_path, salinity_file_path, pressure_input_type, pressure_value, elevation_value):
    all_data = []
    skipped = []
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(directory_path, filename)
            try:
                processed_data = process_data(pressure_input_type, pressure_value, elevation_value, file_path, salinity_file_path)
                all_data.append(processed_data)
            except ValueError:
                # Skip files that don't have a valid miniDOT data format
                skipped.append(filename)

    if not all_data:
        raise ValueError(f"No valid miniDOT data files found in '{directory_path}'. "
                         f"Skipped non-data files: {skipped}" if skipped else
                         f"No .txt files found in '{directory_path}'.")

    # Combine all data into a single DataFrame
    combined_data = pd.concat(all_data)

    # Extract the minimum and maximum dates from the combined data
    min_date = combined_data['Time'].min()
    max_date = combined_data['Time'].max()

    # Decide on pressure or elevation value based on input type
    pressure_or_elevation = pressure_value if pressure_input_type.lower() == 'p' else elevation_value

    if pressure_input_type.lower() == 'p':
        pres_elev = "Pressure used (mbar)"
    else:
        pres_elev = "Elevation used (m)"

    # Create a DataFrame for the header row
    header_info = pd.DataFrame({
        'First Measure Date': [min_date.strftime('%Y-%m-%d')],
        'Last Measure Date': [max_date.strftime('%Y-%m-%d')],
        '{}'.format(pres_elev): [pressure_or_elevation]
    })

    # Concatenate header row with the data
    final_data = pd.concat([header_info, combined_data], ignore_index=True)

    # Define the output directory and the file path
    output_dir = "./outputs"
    output_file = "DO_processed_output.csv"
    output_path = os.path.join(output_dir, output_file)

    # Make sure the directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save the combined data to CSV
    final_data.to_csv(output_path, index=False)

    return final_data   

def process_data(pressure_input_type, pressure_value, elevation_value, do_file_path, salinity_file_path):
    if pressure_input_type.lower() == 'p':
        pressure = pressure_value * 100  # Convert mbar to Pa
    elif pressure_input_type.lower() == 'e':
        pressure = elevation_to_pressure(elevation_value)
    else:
        raise ValueError("Invalid input type")

    # Auto-detect miniDOT file format (header position, separator, decimal char)
    skiprows, sep, decimal = detect_do_file_format(do_file_path)
    data = pd.read_csv(do_file_path, skiprows=skiprows, header=0, sep=sep, decimal=decimal)
    data.columns = data.columns.str.strip()
    normalize_do_columns(data)
    data.rename(columns={'Time (sec)': 'Time'}, inplace=True)
    data['Time'] = pd.to_datetime(data['Time'], unit='s')

    # Read salinity file with flexible column names and timestamp formats
    salinity_data = pd.read_csv(salinity_file_path)
    salinity_data.columns = salinity_data.columns.str.strip()
    # Accept either 'Timestamp' or 'Time' as the datetime column
    if 'Time' in salinity_data.columns and 'Timestamp' not in salinity_data.columns:
        salinity_data.rename(columns={'Time': 'Timestamp'}, inplace=True)
    salinity_data['Timestamp'] = pd.to_datetime(salinity_data['Timestamp'], dayfirst=True)
    data['Salinity'] = data['Time'].apply(lambda x: find_closest_salinity(x.timestamp(), salinity_data))

    # Initialize the processor
    processor = DODataProcessor(pressure)

    # Apply the calculation to the entire dataset
    results = data.apply(lambda row: processor.calculate_corrected_DO(row), axis=1)
    data['Corrected DO (mg/l)'] = results.apply(lambda x: round(x[0], 6))
    data['DO Saturation (%)'] = data.apply(lambda row: processor.calculate_DO_saturation(row), axis=1)
    data['Used Salinity (PSU)'] = results.apply(lambda x: round(x[1], 2))

    # Calculate µmol/kg from 'Corrected DO (mg/l)' and add it to the DataFrame
    data['Corrected DO (umol/kg)'] = (data['Corrected DO (mg/l)'] * 1000) / 31.9988
    data['Corrected DO (umol/kg)'] = data['Corrected DO (umol/kg)'].round(6)

    return data
