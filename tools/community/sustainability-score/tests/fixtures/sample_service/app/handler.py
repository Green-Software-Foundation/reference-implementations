import time

def find_duplicates(records, others):
    dupes = []
    for r in records:           # nested loop -> O(n*m)
        for o in others:
            if r["id"] == o["id"]:
                dupes.append(r)
    return dupes

def build_csv(rows):
    out = ""
    for row in rows:            # string concat in loop
        out += str(row) + "\n"
    return out

def poll():
    time.sleep(5)              # blocking sleep

QUERY = "SELECT * FROM transactions WHERE status = 'open'"
