# A 2.5-year campus-level smart meter database with equipment data for energy analytics

[https://doi.org/10.5061/dryad.k3j9kd5h6](https://doi.org/10.5061/dryad.k3j9kd5h6)

## General Information

1. Description: Accurate campus electricity management is crucial for energy efficiency and optimization. However, comprehensive load data is often lacking, hindering research efforts. This paper presents a dataset from HKUST, featuring over 1,400 meters across more than 20 buildings, collected over 2.5 years. The raw data was refined for research using the Brick Schema, enabling studies in load pattern recognition, fault detection, demand response strategies, and load forecasting.
2. Date of data collection: 2022-01-01 to 2024-05-27.
3. Geographic data collection location: Sai Kung District, Hong Kong, China(22.3363°N 114.2634°E).
4. Goal: This dataset is tailored for users engaged in energy management and analysis, featuring detailed internal equipment data. It supports applications in pattern recognition, fault diagnosis, demand response, and load forecasting.

## Data and file structure

This dataset encompasses a comprehensive 2.5-year record of campus-level energy usage, meticulously categorized into Raw and Clean datasets, each containing time-series data and metadata. The dataset supports detailed energy management and analysis, focusing on internal equipment metrics and general energy consumption patterns.

1. Raw Dataset: Includes unprocessed records of energy usage and equipment data.
   * Time-series data: Stored in .xlsx format, this data captures real-time energy usage across various campus locations and equipment. Each file represents a unique metering point, documenting electricity usage in its original form. There are a total of 1394 files, with filenames typically following the format `GUI.NO.D0001.xlsx`
   * Metadata: Stored in `HKUST_Meter_Metadata.ttl`. This Turtle (.ttl) file is formatted using the Brick Schema and includes metadata detailing the location, equipment, and relationships. For guidance on how to utilize this file, please refer to the documentation available on [GitHub](https://github.com/LiMingchen159/HKUST_Meter_Brick).
2. Clean Dataset: Features data that has been resampled for uniform time intervals, ideal for consistent trend analysis and modeling.
   * Resampled data: Based on the actual intervals of the original data, the dataset has been resampled into four categories: **T15** (15-minute intervals), **T30** (30-minute intervals), **T60** (hourly intervals), and **T1440** (daily intervals). These resampled files facilitate various analyses by providing data in standardized time frames. Stored in .xlsx format. A typical filename looks like `GUI.NO.D0001.xlsx`. The T15 category comprises 403 files, T30 has 645 files, T60 has 255 files, and T1440 has 26 files. Notably, 65 files were excluded due to missing data or data consisting solely of zeros.
   * Metadata: Stored in `HKUST_Meter_Metadata.ttl`. Mirrors the raw dataset's metadata. For guidance on how to utilize this file, please refer to the documentation available on [GitHub](https://github.com/LiMingchen159/HKUST_Meter_Brick).

The dual-format approach (Excel for time-series data and Turtle for metadata) ensures that the dataset is both accessible and comprehensive, supporting a wide range of analytical applications.

## Code/Usage

[The HKUST Data Analysis repository](https://github.com/LiMingchen159/HKUST_Meter_Brick) contains a comprehensive set of scripts for processing and analyzing electricity consumption data from the Hong Kong University of Science and Technology. The repository is organized into several modules:

* **Data Preprocessing**: Standardizes raw data into consistent intervals.
* **Lighting Analysis**: Processes and visualizes lighting patterns across different floors of academic buildings.
* **Missing Rate Analysis**: Calculates and visualizes missing data rates on an hourly basis and across different sampling intervals.
* **Data Querying**: Extracts building, equipment, and zone-related information using SPARQL.

