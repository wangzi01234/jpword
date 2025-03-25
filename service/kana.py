import mysql.connector
from mysql.connector import Error
from collections import defaultdict
import os
from dotenv import load_dotenv

load_dotenv()

def get_db():
    
    try:
        db = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT",'3306')),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE")
        )
        return db
    except Error as e:
        raise Exception(f"Database connection failed: {str(e)}")


# 统一表格配置（可扩展）
TABLE_CONFIGS = [
    {
        "title": "清音",
        "colspan": 5,
        "prefixes": ['a', 'ka', 'sa', 'ta', 'na', 'ha', 'ma', 'ya', 'ra', 'wa', 'n']
    },
    {
        "title": "浊音/半浊音",
        "colspan": 5,
        "prefixes": ['ga', 'za', 'da', 'ba', 'pa']
    }
]

async def get_kana_data():
    # 获取数据库连接
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        # 单次查询获取全部数据
        cursor.execute("SELECT * FROM kana ORDER BY slug")
        kanas = cursor.fetchall()
        
        # 构建分组字典（自动处理前缀）
        groups = defaultdict(list)
        for kana in kanas:
            prefix, _ = kana['slug'].split('-')
            groups[prefix].append(kana)
        
        # 生成表格数据
        tables = []
        for config in TABLE_CONFIGS:
            table_rows = []
            for prefix in config['prefixes']:
                if prefix in groups:
                    # 统一排序逻辑
                    sorted_row = sorted(groups[prefix], 
                                        key=lambda x: int(x['slug'].split('-')[1]))
                    table_rows.append(sorted_row)
            
            tables.append({
                "title": config['title'],
                "colspan": config['colspan'],
                "rows": table_rows
            })
    finally:
        cursor.close()
        db.close()
    return tables

def get_kana_dict():
    """
    获取所有假名与slug的映射字典
    返回格式：{'あ': 'a-1', 'ア': 'a-1', 'か': 'ka-1', 'カ': 'ka-1', ...}
    """
    db = get_db()
    cursor = db.cursor(dictionary=True)
    kana_dict = {}
    
    try:
        cursor.execute("SELECT hiragana, katakana, slug FROM kana")
        all_kana = cursor.fetchall()
        
        for kana in all_kana:
            # 将平假名和片假名都映射到同一个slug
            kana_dict[kana['hiragana']] = kana['slug']
            kana_dict[kana['katakana']] = kana['slug']
        # print(kana_dict)    
    finally:
        cursor.close()
        db.close()
    
    return kana_dict

def search_words(search):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
                SELECT * FROM word 
                WHERE japanese LIKE %s 
                OR kana LIKE %s 
                OR chinese LIKE %s
                """
        params = (f"%{search}%", f"%{search}%", f"%{search}%")
        cursor.execute(query, params)
        words = cursor.fetchall()
        
        for word in words:
            kana_list = word['kana'].split(',')
            slugs = []
            for k in kana_list:
                cursor.execute("SELECT slug FROM kana WHERE hiragana = %s OR katakana = %s", (k.strip(), k.strip()))
                result = cursor.fetchone()
                slugs.append(result['slug'] if result else '#')
            word['slugs'] = slugs
    finally:
        cursor.close()
        db.close()
    return words

def get_words_by_slug(slug):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM kana WHERE slug = %s", (slug,))
        kana = cursor.fetchone()
        if not kana:
            raise HTTPException(status_code=404, detail="Kana not found")
        cursor.execute("""
        SELECT *
        FROM word
        WHERE kana LIKE CONCAT('%%', %s, '%%')
        OR kana LIKE CONCAT('%%', %s, '%%')
        """, (kana['hiragana'], kana['katakana']))

        words = cursor.fetchall()
        kana_dict = get_kana_dict()

    finally:
        cursor.close()
        db.close()
    return words, kana_dict, kana

def search_all_words():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        query = """
                SELECT * FROM word order by id
                """
        cursor.execute(query)
        words = cursor.fetchall()
        
        for word in words:
            kana_list = word['kana'].split(',')
            slugs = []
            for k in kana_list:
                cursor.execute("SELECT slug FROM kana WHERE hiragana = %s OR katakana = %s", (k.strip(), k.strip()))
                result = cursor.fetchone()
                slugs.append(result['slug'] if result else '#')
            word['slugs'] = slugs
    finally:
        cursor.close()
        db.close()
    return words