import pymysql
from config import host, user, password, port, db_name

db_params = {
    'host': host,
    'port': port,
    'user': user,
    'password': password,
    'database': db_name,
}

db = pymysql.connect(**db_params)

cursor = db.cursor()

cursor.execute("""
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    order_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    medicine_id INT,
    quantity INT,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (medicine_id) REFERENCES medicines(id)
)
""")

db.commit()

db.close()
