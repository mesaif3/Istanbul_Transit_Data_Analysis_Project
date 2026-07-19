# SQL operations used in Downloader.ipynb

This document summarizes the SQL statements executed by `Downloader.ipynb` and explains how each query is used by the notebook workflow. The comments below are written to match the logic in the Python functions that build and run the SQL.

The SQL in this notebook is mainly used for:

- cleaning and compressing imported transport data
- exporting cleaned data to Parquet/CSV files
- discovering exported files
- building and updating date tables
- extracting and cleaning dimension tables
- loading data into DuckDB tables for analysis
- exposing the database through the Quack server

---

## 1) Cleaning and compressing the raw dataset

Used by: `clean_dataset()`

Purpose:
This query is generated from the notebook parameters `kept_columns` and `spread_columns`. It removes unnecessary columns and aggregates numeric values that were spread across multiple rows.

```sql
-- This query is built in Python by the clean_dataset() function.
-- It is used to compress vertically spread data into a cleaner table.
SELECT
    -- These columns identify a unique record in the output table.
    transition_date,
    transition_hour,
    product_kind,
    transaction_type_desc,
    town,
    line_name,
    station_poi_desc_cd,

    -- These values were spread across multiple rows and must be summed.
    SUM(TRY(number_of_passage::INTEGER)) AS number_of_passage,
    SUM(TRY(number_of_passenger::INTEGER)) AS number_of_passenger
FROM
    dataset
GROUP BY
    -- The grouping columns must match the natural identity of the row.
    transition_date,
    transition_hour,
    product_kind,
    transaction_type_desc,
    town,
    line_name,
    station_poi_desc_cd;
```

---

## 2) Exporting cleaned data to a file

Used by: `save_to_file()`

Purpose:
After the data has been cleaned, the notebook writes the result to a file using DuckDB `COPY`. The notebook can also fall back to PyArrow if DuckDB export fails.

```sql
-- This query is wrapped inside a COPY statement by save_to_file().
-- It selects the cleaned columns and writes them to the target export file.
COPY (
    SELECT
        transition_date,
        transition_hour,
        product_kind,
        transaction_type_desc,
        town,
        line_name,
        station_poi_desc_cd,
        number_of_passage,
        number_of_passenger
    FROM
        dataset
) TO
    'export/query/hourly_transportation_202301.parquet'
(FORMAT parquet);
```

Notes:

- The actual file location is generated dynamically from the notebook export parameters.
- The file format is controlled by `export_format`, which is set to `PARQUET` in the notebook.

---

## 3) Discovering exported files

Used by: `get_export_info()`

Purpose:
This query searches the export directories for files that match the naming pattern built from the notebook parameters. The result is used to build a dataframe that tracks available export files.

```sql
-- This query is built from the notebook's export prefix, suffix, and export folders.
-- It searches both predownloaded exports and queried exports for matching files.
SELECT *
FROM glob('export/predownload/hourly_transportation_*2023*.parquet')
UNION ALL
SELECT *
FROM glob('export/query/hourly_transportation_*2023*.parquet');
```

Why it matters:

- The notebook uses this to know which files already exist.
- It helps the loader decide whether to create, update, or skip a table.

---

## 4) Checking whether a table already exists

Used by: `priority_based_sql_loader()`

Purpose:
Before inserting data into a target table, the notebook checks whether that table already exists in DuckDB. This is used to either replace it or add to it.

```sql
-- This query checks whether a table exists in the current DuckDB database.
SELECT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_name = 'hourly_transportation_all'
);
```

Why it matters:

- If the table exists and reload is enabled, the notebook replaces it.
- If the table does not exist, the notebook creates it first.

---

## 5) Building the date table

Used by: `date_loader()`

Purpose:
The notebook uses SQL to collect available dates from all imported tables and then create a `dates` table with year, quarter, month, day, and weekday information.

### 5.1 Collecting distinct dates from all relevant tables

```sql
-- This query collects all distinct transition dates from multiple tables.
-- In the notebook, the query is built dynamically from all valid table names.
WITH all_dates AS (
    SELECT DISTINCT transition_date FROM table_1
    UNION
    SELECT DISTINCT transition_date FROM table_2
    UNION
    ...
    SELECT DISTINCT transition_date FROM table_n
),
WITH scanned_dates AS (
    SELECT DISTINCT transition_date::DATE AS transition_date
    FROM (SELECT * FROM all_dates)
    ORDER BY transition_date
)
```

### 5.2 Generating a full range of dates from the the earliest and latest dates

```sql
-- This query finds the earliest date from each table and then
-- combines the results to determine the overall earliest date.
WITH first_dates AS (
    SELECT DISTINCT transition_date FROM table_1
    ORDER BY transition_date ASC LIMIT 1
    UNION
    ...
    SELECT DISTINCT transition_date FROM table_n
    ORDER BY transition_date ASC LIMIT 1
),

-- This query finds the latest date from each table and then
-- combines the results to determine the overall latest date.
WITH last_dates AS (
    SELECT DISTINCT transition_date FROM table_1
    ORDER BY transition_date DESC LIMIT 1
    UNION
    ...
    SELECT DISTINCT transition_date FROM table_n
    ORDER BY transition_date DESC LIMIT 1
),

-- This query creates a continuous date range from the earliest to the latest date.
WITH generated_dates AS (
    SELECT CAST(range AS DATE) AS transition_date
    FROM range(
        (SELECT transition_date FROM first_dates LIMIT 1),
        (SELECT transition_date FROM last_dates LIMIT 1) + INTERVAL 1 DAY,
        INTERVAL 1 DAY
    )
);
```

### 5.3 Enriching dates with calendar information

```sql
-- This query transforms the generated date range into a calendar table.
WITH table_date AS (
    SELECT
        transition_date,
        CAST(date_part('year', transition_date) AS INT) AS Year,
        'Q' || CAST(date_part('quarter', transition_date) AS INT) AS Quarter,
        strftime(transition_date, '%B') AS Month_Name,
        CAST(date_part('month', transition_date) AS INT) AS Month_No,
        CAST(date_part('day', transition_date) AS INT) AS Day,
        strftime(transition_date, '%A') AS Weekday_Name,
        CAST(date_part('isodow', transition_date) AS INT) AS Weekday_No
    FROM
        -- either scanned_dates or generated_dates
        table_dates;
)
```

### 5.4 Saving the date table

```sql
-- This statement creates or replaces the dates table in DuckDB.
CREATE OR REPLACE TABLE 'dates' AS
SELECT *
FROM table_date;
```

---

## 6) Extracting dimension data from processed files

Used by: `pull_dims()`

Purpose:
The notebook extracts user-defined dimension information from each processed dataset and writes it to disk as separate export files.

```sql
-- This query counts how often each unique dimension combination appears.
-- The columns are defined by the dims dictionary in the notebook.
SELECT
    line,
    line_name,
    transport_type_id,
    COUNT(*) AS count
FROM
    file
GROUP BY
    line,
    line_name,
    transport_type_id;
```

Why it matters:

- These dimension exports are later used to build clean dimension tables.
- The count column helps identify the most common or most reliable row.

---

## 7) Cleaning and ranking dimension data

Used by: `dims_accountant()`

Purpose:
The notebook creates:

- an error table that records ambiguous dimension rows
- a clean dimension table that keeps the most common value for each dimension key

### 7.1 Cleaning the dimension values

```sql
-- This query trims whitespace and removes quotation marks from the cleaning column.
-- It then aggregates the cleaned values by the relevant dimension columns.
SELECT
    line,
    line_name,
    transport_type_id,
    SUM(count) AS count
FROM (
    SELECT
        TRIM(REPLACE(line, '"', '')) AS line,
        line_name,
        transport_type_id,
        SUM(count) AS count
    FROM
        line_temp
    GROUP BY
        line,
        line_name,
        transport_type_id
) t
GROUP BY
    line,
    line_name,
    transport_type_id;
```

### 7.2 Creating an error table

```sql
-- This query creates a dimension error table.
-- It links each cleaned dimension row with an error vector based on repeated conflicts.
CREATE OR REPLACE TABLE 'line_error' AS
SELECT
    t1.line,
    t1.line_name,
    t1.transport_type_id,
    t1.count,
    t2.Error_Vector
FROM (
    SELECT *
    FROM temp
) t1
LEFT JOIN (
    SELECT
        line_name,
        COUNT(*) AS Error_Vector
    FROM
        temp
    GROUP BY
        line_name
) t2
ON t1.line_name = t2.line_name;
```

### 7.3 Creating the clean dimension table

```sql
-- This query ranks dimension rows by how often they appear,
-- then keeps only the top-ranked row for each dimension key.
WITH ranked_partition AS (
    SELECT
        line,
        line_name,
        transport_type_id,
        count,
        DENSE_RANK() OVER (
            PARTITION BY line_name
            ORDER BY count DESC
        ) AS rank
    FROM
        line_error
)
CREATE OR REPLACE TABLE 'line_dim' AS
SELECT
    line,
    line_name,
    transport_type_id
FROM
    ranked_partition
WHERE
    rank = 1;
```

---

## 8) Loading exported parquet files into the database

Used by: `priority_based_sql_loader()`

Purpose:
The notebook creates or fills tables from parquet files. The loader supports:

- no partitioning
- yearly partitioning
- monthly partitioning

### 8.1 Create an empty table schema

```sql
-- This query creates an empty table with the same schema as the sample parquet file.
-- It is used so the loader can insert rows into a table without loading data yet.
CREATE OR REPLACE TABLE 'hourly_transportation_all' AS
SELECT *
FROM read_parquet('sample_export.parquet')
WHERE 1 = 0;
```

### 8.2 Insert data into the table

```sql
-- This query inserts rows from an exported parquet file into the target table.
INSERT INTO 'hourly_transportation_all'
SELECT *
FROM read_parquet('hourly_transportation_202301.parquet');
```

Why it matters:

- This is the main warehouse-loading step.
- It lets the notebook build tables from exported files without manually copying data.

---

## 9) Loading dimension tables from exported files

Used by: `extracted_dims_loader()`

Purpose:
The notebook loads the cleaned dimension exports generated earlier into DuckDB tables.

```sql
-- This query loads a dimension table from an exported parquet file.
CREATE OR REPLACE TABLE 'line_dim' AS
SELECT *
FROM read_parquet('export/line_dim.parquet');
```

The notebook repeats this approach for each dimension table defined in the `dims` dictionary.

---

## 10) Loading dimension tables from Excel sheets

Used by: `dims_loader()`

Purpose:
The notebook can also load manually maintained dimension tables from Excel sheets into DuckDB.

```sql
-- This query creates or replaces a DuckDB table from a pandas dataframe.
-- In the notebook, the dataframe is created from an Excel sheet.
CREATE OR REPLACE TABLE 'ticket_dim' AS
SELECT *
FROM dim_table;
```

---

## 11) Running and stopping the Quack server

Used by: notebook cells at the end of the pipeline

Purpose:
The notebook can expose the DuckDB database through a local Quack server so external tools can query it.

```sql
-- Starts the Quack server on localhost using the provided token.
CALL quack_serve('quack:localhost', token = 'super_secret');
```

```sql
-- Stops the Quack server previously started by the notebook.
CALL quack_stop('quack:localhost');
```

---

## Summary

The SQL used in Downloader.ipynb is responsible for:

- transforming raw transport data into a compact analytical form
- exporting that data to parquet files
- discovering and tracking exported files
- building a date dimension table
- extracting and cleaning dimension tables
- loading data into DuckDB for analysis
- exposing the database through Quack

These queries are mostly generated dynamically in Python, but they follow the same patterns shown above.
