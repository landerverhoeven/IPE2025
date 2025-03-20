# Optimization Project for PV System Calculations

## Overview
This project aims to optimize the calculations related to a photovoltaic (PV) system using a semi-advanced optimization algorithm. The initial implementation is provided in `average_yearly.py`, which includes constants for the system, data loading, and preprocessing of irradiance and load data. The optimization is handled in `optimizer.py`, where various parameters such as panel efficiency and tilt angle are fine-tuned for improved performance.

## Project Structure
```
optimization-project
├── data
│   ├── Irradiance_data.xlsx
│   └── Load_profile_8.xlsx
├── src
│   ├── average_yearly.py
│   ├── optimizer.py
│   └── utils.py
├── requirements.txt
└── README.md
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd optimization-project
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
- To run the initial PV system calculations, execute:
  ```
  python src/average_yearly.py
  ```

- To optimize the parameters, run:
  ```
  python src/optimizer.py
  ```

## Dependencies
This project requires the following Python libraries:
- pandas
- numpy
- matplotlib

Ensure that these libraries are installed in your Python environment.