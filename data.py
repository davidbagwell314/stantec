import csv

if __name__ == "__main__":
    file = open("data/bulk.csv")
    reader = csv.reader(file)
    for row in reader:
        for element in row:
            print(element)