from django.core.management import BaseCommand
import psycopg2
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):
        # Получение данных подключения из настроек базы данных
        db_port = settings.DATABASES['default']['PORT']
        db_host = settings.DATABASES['default']['HOST']
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']

        print(f"Подключение к базе данных {db_name} на хосте {db_host} и порту {db_port} с пользователем {db_user}.")

        conn = None
        try:
            # Подключение к серверу PostgreSQL
            conn = psycopg2.connect(
                dbname='postgres',  # Подключаемся к стандартной базе данных для создания новой
                user=db_user,
                password=db_password,
                host=db_host,
                port=db_port
            )
            conn.autocommit = True  # Включаем автокоммит

            # Создание курсора для выполнения команд
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE {settings.DATABASES['default']['NAME']};")
            print(f"База данных {settings.DATABASES['default']['NAME']} успешно создана.")
        except psycopg2.Error as ex:
            print(f"Ошибка при создании базы данных: {ex}")
        finally:
            if conn:
                cursor.close()  # Закрываем курсор
                conn.close()  # Закрываем соединение

