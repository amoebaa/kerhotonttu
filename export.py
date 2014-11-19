from datetime import datetime
import sqlite3

def perverse_format_datetime(orig):
    dt = datetime.strptime(orig, "%Y-%m-%d %H:%M");
    return dt.strftime("%M-%H-%d-%m-%y");

def main():
    db = sqlite3.connect("rawdata.sqlite")

    c = db.cursor()
    data = []
    c.execute("SELECT * FROM rawdata")
    with open('rawdata.csv', 'w') as f:
        f.write("aika,lampo,ovi,valo\n")
        for row in c.fetchall():
            formatted_row = (
                perverse_format_datetime(row[0]),
                str(row[1]),
                str(row[2]),
                str(row[3]))
            f.write(",".join(formatted_row) + "\n")

if __name__ == '__main__':
    main()
