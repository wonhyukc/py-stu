import csv

input_file = "output/wb01-mid.csv"
output_file = "output/wb01-mid.csv"

with open(input_file, "r", encoding="utf-8") as f:
    reader = list(csv.reader(f))
    header = reader[0]
    data = reader[1:]

# Sort data by the first column (Student ID)
data.sort(key=lambda x: x[0])

with open(output_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(data)

print("Sorted successfully.")
