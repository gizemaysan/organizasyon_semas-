import pyodbc
import pandas as pd
from flask import Flask, render_template
from flask import send_from_directory
import os

app = Flask(__name__)

# bağlantı kontrol fonksiyonu
def test_db_connection():
    try:
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=NAME OF SERVER;DATABASE=NAME OF DATABASE;UID=NAME OF USER;PWD=PASSWORD')
        print("Bağlantı başarılı!")
        conn.close()
    except pyodbc.Error as e:
        print(f"Veritabanına bağlanırken hata oluştu: {e}")

test_db_connection()

# Veritabanı bağlantısı ve veri çekme fonksiyonu
def get_data_from_db():
    try:
        # SQL Server bağlantısı
        conn = pyodbc.connect('DRIVER={SQL Server};SERVER=NAME OF SERVER;DATABASE=NAME OF DATABASE;UID=NAME OF USER;PWD=PASSWORD')

        # SQL sorgusu
        query = """
        WITH EmployeeHierarchy AS (
            SELECT id, adi_soyadi, ust_amir_id, 0 AS Level
            FROM NAME OF TABLE
            WHERE id = ID DEĞERİNİ GİRİN  -- Bu kişinin altındaki çalışanları çekiyoruz

            UNION ALL

            SELECT e.id, e.adi_soyadi, e.ust_amir_id, eh.Level + 1
            FROM NAME OF TABLE e
            INNER JOIN EmployeeHierarchy eh ON e.ust_amir_id = eh.id
        )
        SELECT id, adi_soyadi, ust_amir_id, Level
        FROM EmployeeHierarchy
        ORDER BY Level, adi_soyadi;
        """

        # SQL sorgusunu çalıştır ve veriyi pandas DataFrame'e çek
        df = pd.read_sql(query, conn)
        conn.close()

        # NVARCHAR'ı INTEGER'a çevir
        df['id'] = pd.to_numeric(df['id'], errors='coerce')
        df['ust_amir_id'] = pd.to_numeric(df['ust_amir_id'], errors='coerce')

        # **Başlangıç ID'yi belirle**
        root_id = df[df['Level'] == 0]['id'].values[0] if not df.empty else None

        return df, root_id  # Root ID'yi de döndür

    except pyodbc.Error as e:
        print(f"Database error occurred: {e}")
        return pd.DataFrame(), None  # Hata durumunda boş dataframe ve None döndür

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame(), None  # Hata durumunda boş dataframe ve None döndür


# Ağaç yapısına dönüştürme fonksiyonu
def build_tree(data, parent_id):
    print(f"Building tree for parent_id: {parent_id}")
    tree = []
    try:
        for _, row in data[data['ust_amir_id'] == parent_id].iterrows():
            node = {
                'id': row['id'],
                'adi_soyadi': row['adi_soyadi'],
                'children': build_tree(data, row['id'])  
            }
            tree.append(node)
    except Exception as e:
        print(f"Error while building tree: {e}")
    return tree

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    try:
        # Veriyi al
        data, root_id = get_data_from_db()
        
        if data.empty or root_id is None:
            return "Veritabanından veri çekilemedi!", 500  

        # Ağaç yapısını oluştur
        tree = build_tree(data, root_id)  
        
        print(f"Ağaç yapısı: {tree}")  # Ağaç yapısını terminalde yazdır

        return render_template('index.html', tree=tree)

    except Exception as e:
        print(f"Error in index route: {e}")
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=True)
