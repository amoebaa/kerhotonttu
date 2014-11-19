from datetime import datetime
import sqlite3

def inverse_format_datetime(orig):
    dt = datetime.strptime(orig, "%M-%H-%d-%m-%y");
    return dt.strftime("%Y-%m-%d %H:%M");

def main():
    db = sqlite3.connect("rawdata.sqlite")

    db.execute(
        '''CREATE TABLE IF NOT EXISTS rawdata
           (aika TEXT, -- Vaatii tietyn formaatin
            lampo INTEGER, -- oispa kaljaa
            ovi INTEGER,
            valo INTEGER);''')
    
    c = db.cursor()
    data = []
    with open('rawdata.csv') as f:
        f.readline() # Discard first line
        for line in f:
            row = line.split(',')
            c.execute('''INSERT INTO rawdata VALUES
                           (?, ?, ?, ?)''',
                           (inverse_format_datetime(row[0]),
                            row[1],
                            row[2],
                            row[3]))
    db.commit()

if __name__ == '__main__':
    main()
