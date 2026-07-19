# Istanbul Transit Data Project

## Purpose & Method

**Challenge:** A metropolitan city like Istanbul is bound to have competitve costs of living, as well as running a business. While people are forced into commutes due to housing situations, and business needing to manage their assets in a competitive market, management teams need to rely on gatherable data to make insights and forecast future trends.

**Solution:** An ETL pipeline can facilitate the collection of data from accessable data, such as the [Hourly Public Transport Data Set](https://data.ibb.gov.tr/en/dataset/hourly-public-transport-data-set), storing data in a specialized format for direct use and quality assesment through the use of BI tools.

## Data Pipeline Architecture

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
When looking at the summaries of the extracted dim information, a few quick insights come to mind:

1. The dataset seems to have mismatched dimensions in a notable portion of it's rows.
2. The Line Dim seems to have many mismatches but it seems the data is acceptable enough unless we wish to look at data under the "RAYLI" category in specific.
3. The Ticket Dim seems to have far too error prone to make any direct analysis using it before correcting it.
4. The Road Dim seems to be free of any conflicting dimensional properties.

![](image-1.png)
When browsing the more detailed page in the dashboard, we can dive deeper into the possible regions of conflict and determine where we need to direct our attention. This example of the Line Dimensional information offers such insights:

- ~16.9% of the Rayli data is cause for error, filtering for it, shows the problems lie in lines M1 and M5, which have two entries each for different transport_type_id (They are listed as Rayli and as either Deniz or Otoyol).
- ~2.3% of the Otoyol data is cause for error. Filtering for it will show that 34A has two entries for different transport_type_id, while the rest have different entries for different line routes.
- When the Permissible Conflict Rate is 0.5%, the only lines worth addressing would be M1, M5, and 34A, in that order.

# Transit Operations Manager Dashboard

In Istanbul, a significant portion of the population rely heavily on the public transportation system to commute around the city. A transit operations manager is expected to provide adequate routes and provide acceptable quality of life standards to the passangers, regardless of status. This dashboard uses Hourly Transportation data from 2023-2024 to answer a few questions.

A few measures are frequently used in the graph axis', which makes them worth addressing for context:

- **Median Total Hourly Passages:** The number of passages are collected in window sizes of one hour, and we take the median across these bins.
- **Median Total Daily Passages:** The number of passages are collected in window sizes of one day, and we take the median across these bins.
- **Median Total Monthly Passages:** The number of passages are collected in window sizes of one month, and we take the median across these bins.
- **The use of medians over averages:** When using medians, we make the insight more robust against outliers and varying sample sizes. By comparing the Median Total Daily Passages and the Median Total Monthly Passages, we can quickly detect the presence of outliers between the day-to-day windows.
- **Coefficient of Variation:** The coefficient of variation is specifically that of the number of passangers column. The standard deviation is divided by the average to show relative variablity by categories.
- **Erraticity:** is the ratio of the Median Total Monthly Passages to the Median Total Daily Passages - 30. This gives a rate and direction of skewness in the median total daily passages by the grouping categories.
- **Popularity Vector:** A measure that is used to see how popular a line is with a certain card type. (Popularity of the line amongst all lines) \* (How much of the transactions are by a specific card type)

## Transit info summary

![](transit/Transit_sql_quack-1.png)

- How many passenges can be expected per hour, day, or month?
  - The median of passages was 282K per hour, 7M per day, and 201M per month. More specific information can be provided when filtering for certain lines or stations.
- How are the passages distributed accross types of transport?
  - ~57% of the daily passages are on the Otoyol lines, and ~43% of the daily passages are on the Rayli lines. The Deniz lines were too low to consider.
- What are the three most common card types?
  - At ~43% of monthly transactions, "INDIRIMLI1" is the most commonly used card, which is most likely the discounted card given to students, teachers, and people older than 60.
  - At ~39% of monthly transactions, "TAM" is the 2nd most commonly used card, which is most likely the base, undiscounted card that is available to everyone.
  - At ~13% of monthly transactions, "UCRETSIZ" is the 3rd most commonly used card, which is most likely the free pass card given to mothers, disabled people, veterans, people older than 65, and so on.

When sorting by the Line Name of the relevant transactions, we can look at the lower half of the dashboards to answer these questions:

- What are the top 5 used lines?
  - 34, Marmaray, M2, T1, and M1. However, most of them are Rayli lines.
- What can you say about the distribution of the passanges accross the lines?
  - Most of the passages are recorded to be on Rayli and Otoyol lines. However, most of the passages happen in a handful of lines.
  - Almost all of the Rayli lines have very high passages with low Erraticity, while the Otoyol passages are distributed accross a large amount of different lines is lower amounts but with a certain Erraticity, with the exception of 34 and 34A, the metrobus lines, which behave similiar to the Rayli lines.

![](transit/Transit_sql_quack1-1.png)
When sorting by the Station Name of the relevant transactions, we can look at the lower half of the dashboards to answer these questions:

- What are the top 5 most used stations?
  - We can see that most of the Otoyol transactions don't include a station name! Hence, we cannot infer much on bus stations.
  - The next top stations are Yenikapi, Zeytinburnu, Sisli 2 Kuzey, Yenikapi-2, and Mecidiyekoy, which are a mix of Rayli and Otoyol lines.
  - It can be noted that the less popular Deniz stations are seen competing with the stations of the other line types. This is likely due to the Deniz lines only having 2 stations per line, as opposed to the 10+ stations found on Otoyol and Rayli lines.
- What can you say about the distribution of the passanges accross the lines?
  - The stations are more spread out in use for Rayli lines, but they still sit on the higher end of total passangers.
  - The Deniz stations either have a very large amount of passengers (like USKUDAR) or very low amount.
  - We can see that the Otoyol lines are all grouped together in one clump because they dont include the station in the transactions.

## Transit info deep dive

![](transit/Transit_sql_quack-2.png)

- What are the highest traffic hours?
  - Weekdays have peaks at 8:00AM and 6:00PM, which corresponds to the 9-5 workday.
  - Weekends have much lower peaks around 12:00PM and 6:00PM.
- How do the passages per line vary by the season?
  - High variations, of ~ 80% relative to the mean, are seen around August and drop by the end of November.
- How are the line passages affected by the day of the week?
  - Weekdays hold roughly similiar values regardless of the line type, while weekends see a dip in Otoyol and Rayli, while Deniz lines see more use.
- Which lines require more attention for accesibility infrastructure?
  - 34, Marmaray, T1, M1, and T4 are the top 5 lines by popularity when filtered for the "UCRETSIZ" card. This is sorted by a joint probablity vector to show how popular a line is amongst users with accessibility needs.

![](transit/Transit_sql_quack1-2.png)

- What months see the most and least daily traffic?
  - The weekdays of May and October tend to see the most daily traffic with a median of 8.2M, an increase of ~17% of the global median.
  - August sees the least traffic with a median of ~6.3M, a decrease of ~10% from the global median.
- What months are more likely to have less traffic?
  - The erraticity in the months of August to September are highly negative, which suggests a skewness towards low-activity in the daily medians of these months.

![](transit/Transit_sql_quack2-1.png)

- How do the insights change when grouped differently?
  - The erraticity and daily passages exhibit very similiar behaviors when grouped by card type instead of by line type. This implies that the cause for the activity is not dependant on the category.

## Transit info relationship model

![](transit/Transit_sql_quack_model.png)

Information on the columns can be found at [Hourly Public Transport Data Set](https://data.ibb.gov.tr/en/dataset/hourly-public-transport-data-set)

The star schema model includes tables that are chached or queried from the Quack Server as such:

- **dates:** This table is cached and it holds the dates and additional information, such as transition_date as primary key, day number, month name, year, ets.
- **line_dim:** This table is cached and it holds information of the line such as, line name as primary key, line route, and line type as foreign key.
- **road_dim:** This table is cached and it holds information the line type with the index as the primary key
- **ticket_dim:** This table is cached and holds whether the transaction type is a transfer or not. It holds the transaction_type_desc as primary key and transfer_type
- **hourly_transportation_all:** Is the facts table that is queried from the server using direct query.
