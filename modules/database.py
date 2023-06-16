# -*- coding: utf-8 -*-
import sqlite3

connection = sqlite3.connect('/home/aid/PycharmProjects/marion_theatre/bd/reservation.db')
cursor = connection.cursor()


class SQLighter:

    def __init__(self, database):
        """Подключаемся к БД и сохраняем соединения"""
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def get_reservation(self):
        """Получаем данные по количеству резерваций"""
        with self.connection:
            return self.cursor.execute(
                "SELECT user_locality, SUM(weight_data) FROM user_data GROUP BY user_locality").fetchall()

    def user_add_reservation(self, buy_product, user_locality, weight_data, userinfo_id):
        """Добавляем данные в таблицу"""
        with self.connection:
            return self.cursor.execute("INSERT INTO user_data (buy_product, user_locality, weight_data, userinfo_id)"
                                       "VALUES (?, ?, ?, ?)", (buy_product, user_locality, weight_data, userinfo_id))

    def get_user_id(self):
    # Получаем данные по количеству резерваций с указанием ID пользователя
        with self.connection:
            return self.cursor.execute("SELECT user_locality, userinfo_id, SUM(weight_data) FROM user_data "
                                       "GROUP BY user_locality, userinfo_id").fetchall()

    # Получаем список всех пользователей
    def get_all_users(self):
        return self.cursor.execute(
            "SELECT DISTINCT userinfo_id FROM user_data").fetchall()

    def close(self):
        """Закрываем соединение с БД"""
        self.connection.close()


cursor.execute('''CREATE TABLE IF NOT EXISTS user_data
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                buy_product TEXT NOT NULL,
                user_locality TEXT NOT NULL,
                weight_data INTEGER NOT NULL,
                userinfo_id INTEGER NOT NULL)''')
connection.commit()
