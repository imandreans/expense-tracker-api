import psycopg2
import os
from os.path import join, dirname
from dotenv import load_dotenv
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

conn = psycopg2.connect(host=os.getenv("HOST"), dbname=os.getenv("DB_NAME"), user=os.getenv("USER_DB"),
                        password="12345", port=5432)
cur = conn.cursor()

# cur.execute(f""" INSERT INTO public."User" (username, password, balance) VALUES ('mike', '12345', 1000000)""")
# conn.commit()

cur.execute(""" SELECT * FROM public."User" """)
print([i for i in cur.fetchall()])
cur.close()
conn.close()