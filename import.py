import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO book_info (title, author, year, isbn) VALUES (:title, :author, :year, :isbn)",
                    {"title": title, "author": author, "year": year, "isbn": isbn})
        print(f"Added book {title} by {author} from year {year} and isbn: {isbn}")
    db.commit()

if __name__ == "__main__":
    main()
