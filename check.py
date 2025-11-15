import os

folder_path = "/home/tungcutenhoem/Documents/ProjectBigData/BigData3T/data_daily/Banking"

files = os.listdir(folder_path)

for f in files:
    print(f)