import pypyodbc as odbc

# SQL Server bağlantı dizesi
server = 'busrasu.database.windows.net'
database = 'busrasu'
username = 'busrasu'
password = 'B12345678!'
driver = '{ODBC Driver 18 for SQL Server}'  # İhtiyaca göre değiştirilebilir


# Bağlantı dizesi oluşturma
conn_str = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:busrasu.database.windows.net,1433;Database=busrasu;Uid=busrasu;Pwd=B12345678!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;'

# Bağlantı oluşturma fonksiyonu
def get_connection():
    try:
        conn = odbc.connect(conn_str)
        print('Azure SQL database connection is successful.')
        return conn
    except Exception as e:
        print('Database connection is not successful:', e)
        return None
    


