# Istanbul Transit Data Project

## Purpose & Method

**Challenge:** A metropolitan city like Istanbul is bound to have competitve costs of living, as well as running a business. While people are forced into commutes due to housing situations, and business needing to manage their assets in a competitive market, management teams need to rely on gatherable data to make insights and forecast future trends.

**Solution:** An ETL pipeline can facilitate the collection of data from accessable data, such as the [Hourly Public Transport Data Set](https://data.ibb.gov.tr/en/dataset/hourly-public-transport-data-set), storing data in a specialized format for direct use and quality assesment through the use of BI tools.

# Data Pipeline Architecture

![](Pipeline.jpeg)

## Data Source

The data used in this project was acquired from the Istanbul Metropolitan Municipality Open Data Portal. More specifically, it was acquired from the [Hourly Public Transport Data Set](https://data.ibb.gov.tr/en/dataset/hourly-public-transport-data-set). These datasets contain "passenger and journey data using public transportation in Istanbul in hourly terms." For the sake of this project, the datasets were retrieved in .CSV formats, processed and compressed, loaded into an SQL database, and finally visualized in Microsoft Power BI.

## Data Lakehouse

- **Stored CSV data:** These are manually selected and downloaded files.
- **Processed and compressed data:** These are exports of the processing blocks to be used as ready-to-upload references, but are not meant to be loaded directly into BI tools.
- **SQL Database:** A database to be hosted by an SQL server to be queried by the BI tools.

## Data Extraction

- **Excel/Power Query**: By utilizing power query for webscraping, we can keep a spreadsheet of all the available datasets as well as some additional information, such as: Month, Year, ID, and the Download URL of the dataset.
  - Also included is a local query of processed datasets.
- **Manual Download:** The pipeline is built to support the usage of manually downloaded .CSV files, but it is optional.
- **Python Requests:** By using the Pandas library, we retrieve the Download URLs of the datasets from our tracker spreadsheet. Then we pass it into a get request using the Requests library to query for the .CSV data.

## Data Processing

- **Python + DuckDB:** The .CSV data is either loaded or streamed into python memory using the DuckDB library, after which it undergoes a few operations:
  - **Pulling Dims:** The dimensional features are extracted and separated into their respective files by dataset.
  - **Cleaning:** The unnecessary columns are removed and the rows of data are aggregated to reduce the dataset's size.
  - **Exporting:** The produced facts table is exported into a compressed file for long term storage.
- **Apache Arrow:** When the dataset is too large and DuckDB fails to export it using the default parameters, it is streamed into Apache for exporting by chunks.

## SQL Management

- **Python + DuckDB:** The processed files are loaded to update the Server's database.
- **[DuckDB's Quack](https://duckdb.org/quack/):** The Server is hosted through the Quack Remote Protocol using python+DuckDB as the hosting interface.

## Loading

- **[Quack-Net Power BI Connector](https://github.com/CurtHagenlocher/quack-net):** Power BI does not have a native connector for DuckDB's Quack Remote Protocol, so we make use of this third-party connector to stream the data using Directquery.
- **Microsoft Power BI:** The BI tool we used to create visuals in this project.

# Python Script Quick Start

The default values do not need to be modified for the dataset used in this project but they can be for other datasets.

1. Run ` pip install -r requirements.txt`
2. For default settings, "Run All".

**(Optional)** Certain modifications can be made, if desired in these sections:

2. **Script Parameters:**
   - The range of years to process.
   - Change how files are imported/exported.
   - Which columns are to be included in the facts table, and which to be aggregated accross.
   - The name and columns of the dimension tables.

<br>

4. **File Loading and Processing:**
   - `predownloaded_CSV(file_address)` can be run to directly load a file, process it, and export it by it's local machine address. (To run for all available files `process_all_preloaded()`)
   - `query_CSV(query)` can be run to directly request the file, process it, and export it by a query of a row for the tracker spreadsheet. (To run for all retrievable data `process_all_queries()`)
   - `priority_based_looker(row, priority_sorted_columns = ['File_Path', 'CSV_URL'], reprocess = False)` for a Pandas **row** passed into it from reading the tracker spreadsheet, you can modify the columns it checks first by passing in a reordered **priority_sorted_columns** list. To enable overwriting existing exports, set **reprocess** to **True**.

<br>

6. **SQL Database Updating:**
   - `priority_based_sql_loader(priority_sorted_columns = [predownload_export, query_export], reload = True, partition = None)` changing the order of **priority_sorted_columns** will change which of the currently availble types of exports the loader with favor. Changing **reload** to **False** will prevent overwriting of currently existing tables in the database. Change partition to "Month" or "Year" to have the datasets be stored in respective table partitions instead of being grouped all togethor.
   - `dims_loader(sheet_names=["ticket_dim", "line_dim", "road_dim"])` can be used to directly add the dim tables to the database from an excel file containing the dims in separate sheets.

<br>

7. **SQL Server Launching and Terminating:**
   - `quack:localhost` can be modified to change the hosting address.
   - `super_secret` can be modified to change the token.

# Data Quality Assesment

![](image.png)
![](image-1.png)

# Transit info summary

![](transit/Transit_sql_quack-1.png)
![](transit/Transit_sql_quack1-1.png)

# Transit info deep dive

![](transit/Transit_sql_quack-2.png)
![](transit/Transit_sql_quack1-2.png)
![](transit/Transit_sql_quack2-1.png)

# Transit info relationship model

![](transit/Transit_sql_quack_model.png)
