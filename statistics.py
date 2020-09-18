import requests
from bs4 import BeautifulSoup
import os
import pandas
import seaborn
from matplotlib import pyplot


def get_links(department="Освіта", statisctics="Заклади вищої освіти (1990-2020)"):
    """Function gets direct link to statistics table by names of department and statistics itself"""
    # Set URL variables
    DEPARTMENT_URL, STATISTICS_URL = None, None

    # Beautify UKRSTAT html page
    response = requests.get(url=URL)
    soup = BeautifulSoup(response.content.decode(
        "windows-1251"), "html.parser")

    # Find department URL by its name
    for link in soup.find_all('a', href=True):
        for font in link.find_all("font"):
            if department in font.text.strip():
                DEPARTMENT_URL = f"{os.path.dirname(URL)}/{link.get('href')}"

    # Beautify department html page
    response = requests.get(url=DEPARTMENT_URL)
    soup = BeautifulSoup(response.content.decode(
        "windows-1251"), "html.parser")

    # Find statistics URL by its name
    for link in soup.find_all('a', href=True):
        for font in link.find_all("font"):
            if statisctics in font.text.strip():
                STATISTICS_URL = f"{os.path.dirname(DEPARTMENT_URL)}/{link.get('href')}"

    # Return links that were find or None
    return (DEPARTMENT_URL, STATISTICS_URL)


def parse_table(link):
    """Parsing web table into DataFrame"""
    # Initialize raw data table variable
    raw_table, data_start_index = [], 0

    # Beautify html file
    response = requests.get(url=link)
    soup = BeautifulSoup(response.content.decode(
        "windows-1251"), "html.parser")

    # Find table rows, clean them up and save to the raw_table variable
    for index, row in enumerate(soup.find_all("table")[0].find_all("tr")):
        raw_table.append([])
        for cell in row.find_all('td'):
            raw_table[index].append(cell.text.strip('\n\r\t'))

    # Find first row that contains statistics data
    for index, row in enumerate(raw_table):
        if data_start_index is 0 and all(el.replace(',', '', 1).isnumeric() for el in row[1::]):
            data_start_index = index

    # Create an array that contains names of DataFrame rows
    dataframe_rows = []
    for row in raw_table[data_start_index::]:
        dataframe_rows.append(row[0])
        row.pop(0)

    # Add some empty column names or delete them to match number of data columns
    data_columns, name_columns = raw_table[data_start_index], raw_table[data_start_index-1]
    for i in range(abs(len(data_columns) - len(name_columns))):
        name_columns.insert(0, "") if len(data_columns) >= len(
            name_columns) else name_columns.pop(0)

    # Change comma-separeted float numbers to point-separated
    for i, row in enumerate(raw_table[data_start_index::]):
        for j, cell in enumerate(row):
            raw_table[data_start_index+i][j] = cell.replace(',', '.')

    # Fill DataFrame and convert all numeric values into float
    dataframe = pandas.DataFrame(data=raw_table[data_start_index::])
    dataframe.index = dataframe_rows
    # dataframe.columns = raw_table[data_start_index-1]
    for column in dataframe.columns:
        dataframe[column] = dataframe[column].astype(float)

    # Working with parsed statistics data
    analyze_and_visualize(dataframe)


def analyze_and_visualize(dataframe):
    """Analyzing DataFrame data and visualizing correlation matrix"""
    # Setup variables and create correlation matrix
    mean, variance, deviation = [], [], []
    correlation_matrix = dataframe.corr()

    # For each column calculate mean, variance and standart deviation
    for column in dataframe.columns:
        mean.append(dataframe[column].mean())
        variance.append(dataframe[column].var())
        deviation.append(dataframe[column].std())

    # Add calculated parameters to the dataframe
    dataframe.loc["mean"] = mean
    dataframe.loc["variance"] = variance
    dataframe.loc["deviation"] = deviation
    print(dataframe)

    # Export DataFrame to CSV and Excel files
    with open("statistics.csv", 'w+') as file:
        dataframe.to_csv(file, line_terminator='\n')
    with pandas.ExcelWriter("statistics.xlsx") as writer:
        dataframe.to_excel(writer, engine="xlsxwriter")

    # Create heatmap for correlation matrix and visualize it
    seaborn.heatmap(correlation_matrix, annot=True,
                    cmap=seaborn.color_palette("rocket"))
    pyplot.show()


if __name__ == '__main__':
    URL = "http://www.ukrstat.gov.ua/operativ/oper_new.html"
    DEPARTMENT_URL, STATISTICS_URL = get_links()
    parse_table(STATISTICS_URL)
    print(f"Посилання на таблицю:\t{STATISTICS_URL}")
