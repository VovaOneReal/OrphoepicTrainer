import os
import random
import sys

from PySide6.QtCore import Slot, QTimer, QCoreApplication, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QPushButton, QMessageBox

from ui.About import Ui_About
from ui.Main import Ui_MainWindow
from ui.Results import Ui_Results
from ui.Settings import Ui_Settings
from ui.Training import Ui_Training

import materials.resources

# Todo: изменить стиль новых кнопок в ночном режиме
# Todo: в идеале такие списки как bad_words должны быть множествами. Может быть это поможет упростить код.

# Служебные переменные --------------------------------------------------------

lower_vowels = ("а", "у", "о", "и", "э", "ы", "я", "ю", "е", "ё")
upper_vowels = ("А", "У", "О", "И", "Э", "Ы", "Я", "Ю", "Е", "Ё")

questions_amount = 0  # Количество вопросов для тренировки
bad_words = []  # Запись ID слов, в которых была допущена ошибка
is_repeat = False  # Режим повтора
score = 0  # Счёт верных ответов

# Значения настроек -----------------------------------------------------------

is_dark_mode = False

default_amount = 10
repeats_amount = 3
is_reset_progress = False
is_mix_words = False
is_smart_offer = True
# triggering_threshold = 2
is_auto_next = True
next_question_delay = 1000

# Экземпляры классов окон -----------------------------------------------------

main_window = None
training_window = None


# -----------------------------------------------------------------------------


class MainWindow(QMainWindow):
    """Основное окно."""

    def __init__(self):
        super(MainWindow, self).__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Создаю экземпляры дочерних окон
        self.about = None
        self.settings = None

        # Количество строк (слов) в words.txt
        self.amount_of_lines = None

        global is_dark_mode
        if is_dark_mode:
            # Устанавливаю НОЧНЫЕ иконки для кнопок в окне
            # Кнопка ночного режима
            i_night_mode = QIcon(QPixmap(":/icons/n_night.png"))
            self.ui.pb_night.setIcon(i_night_mode)
            # Кнопка окна авторов
            i_about = QIcon(QPixmap(":/icons/n_about.png"))
            self.ui.pb_about.setIcon(i_about)
            # Кнопка настроек
            i_settings = QIcon(QPixmap(":/icons/n_settings.png"))
            self.ui.pb_settings.setIcon(i_settings)
        else:
            # Устанавливаю СВЕТЛЫЕ иконки для кнопок в окне
            # Кнопка ночного режима
            i_night_mode = QIcon(QPixmap(":/icons/night.png"))
            self.ui.pb_night.setIcon(i_night_mode)
            # Кнопка окна авторов
            i_about = QIcon(QPixmap(":/icons/about.png"))
            self.ui.pb_about.setIcon(i_about)
            # Кнопка настроек
            i_settings = QIcon(QPixmap(":/icons/settings.png"))
            self.ui.pb_settings.setIcon(i_settings)

        # Иконка приложения
        i_app = QIcon(QPixmap(":/icon.ico"))
        self.setWindowIcon(i_app)

        # Даю элементам интерфейса имена для стилей
        self.ui.l_header.setObjectName("header")
        self.ui.pb_start.setObjectName("start-button")
        self.ui.pb_all.setObjectName("context-button")
        self.ui.pb_standart.setObjectName("context-button")
        self.ui.pb_about.setObjectName("context-button")
        self.ui.pb_settings.setObjectName("context-button")
        self.ui.pb_night.setObjectName("context-button")

        # Выдаю функционал кнопкам в главном окне
        self.ui.pb_about.clicked.connect(self.show_about)
        self.ui.pb_settings.clicked.connect(self.show_settings)
        self.ui.pb_start.clicked.connect(self.start)
        self.ui.pb_all.clicked.connect(self.training_all_words)
        self.ui.pb_standart.clicked.connect(self.training_standard)
        self.ui.pb_night.clicked.connect(self.night_mode)

    @Slot()
    def night_mode(self):
        """Включение/выключение тёмной темы."""

        global app, is_dark_mode

        # Включение тёмной темы
        if not is_dark_mode:
            with open("style-dark.qss", "r") as file:
                _app_style = file.read()
                app.setStyleSheet(_app_style)
                is_dark_mode = True

            # Устанавливаю НОЧНЫЕ иконки для кнопок в окне
            # Кнопка ночного режима
            i_night_mode = QIcon(QPixmap(":/icons/n_night.png"))
            self.ui.pb_night.setIcon(i_night_mode)
            # Кнопка окна авторов
            i_about = QIcon(QPixmap(":/icons/n_about.png"))
            self.ui.pb_about.setIcon(i_about)
            # Кнопка настроек
            i_settings = QIcon(QPixmap(":/icons/n_settings.png"))
            self.ui.pb_settings.setIcon(i_settings)

        # Выключение тёмной темы
        elif is_dark_mode:
            with open("style.qss", "r") as file:
                _app_style = file.read()
                app.setStyleSheet(_app_style)
                is_dark_mode = False

            # Устанавливаю СВЕТЛЫЕ иконки для кнопок в окне
            # Кнопка ночного режима
            i_night_mode = QIcon(QPixmap(":/icons/night.png"))
            self.ui.pb_night.setIcon(i_night_mode)
            # Кнопка окна авторов
            i_about = QIcon(QPixmap(":/icons/about.png"))
            self.ui.pb_about.setIcon(i_about)
            # Кнопка настроек
            i_settings = QIcon(QPixmap(":/icons/settings.png"))
            self.ui.pb_settings.setIcon(i_settings)

    @Slot()
    def show_about(self):
        """Показывает окно "Авторы"."""
        self.about = About()
        self.about.show()

    @Slot()
    def show_settings(self):
        """Показывает окно "Настройки"."""
        self.settings = Settings()
        self.settings.show()

    @Slot()
    def start(self):
        """Запускаем тренировку."""

        global default_amount, training_window, questions_amount

        # Запись настроек из файла в глобальные переменные
        extract_settings()

        # Проверяем, число ли это, и если так, то оно будет являться количеством
        # вопросов в сеансе
        try:
            entered_amount = int(self.ui.le_word_amount.text())
        except ValueError:
            entered_amount = default_amount

        self.amount_of_lines = self.get_amount_of_lines()  # Определяем количество строк (слов)
        find_answers(self)  # Составляем ответы к словам / не перемещать строку дальше след. блока

        # Берём введённое кол-во слов
        if entered_amount <= 0 or entered_amount > self.amount_of_lines:
            # Тренируем все слова, если ввели 0 и менее или больше, чем слов
            # в words.txt
            questions_amount = self.amount_of_lines
        else:
            # В остальных случаях записываем введённое кол-во слов
            questions_amount = entered_amount

        training_window = Training()
        training_window.show()
        self.close()

    @Slot()
    def training_all_words(self):
        """Запускает тренировку со всеми словами."""
        self.ui.le_word_amount.setText("0")
        self.start()

    @Slot()
    def training_standard(self):
        """Запускает тренировку со кол-вом слов по-умолчанию."""
        self.ui.le_word_amount.setText(".")
        self.start()

    def get_amount_of_lines(self):
        """Вызывается при всяком запуске тренажёра и нажатии кнопки "Начать".
Просматривает файл words.txt и определяет количество строк (слов) в файле."""

        check_words_existence(self)

        # Открываем соответствующие файлы
        with open("words.txt") as file:
            the_value = len(file.readlines())

        return the_value


class About(QWidget):
    """Окно "Авторы"."""

    def __init__(self):
        super(About, self).__init__()

        self.ui = Ui_About()
        self.ui.setupUi(self)

        self.setAttribute(Qt.WA_QuitOnClose, False)  # Закрываем окно, если оно последнее

        # Иконка приложения
        i_app = QIcon(QPixmap(":/icon.ico"))
        self.setWindowIcon(i_app)

        self.ui.pb_changelog.setObjectName("link")

        self.ui.pb_changelog.clicked.connect(self.open_news)

        global is_dark_mode
        if is_dark_mode:
            self.ui.l_link.setText(
                '<a href="https://github.com/VovaOneReal/OrthoepicTrainer"><span style=" text-decoration: underline; color:#3091f2;">Проект на GitHub</span></a>')

        # Позволяю открывать внешние ссылки
        self.ui.l_link.setOpenExternalLinks(True)

    @Slot()
    def open_news(self):
        if not os.path.isfile("NEWS.txt"):
            QMessageBox.question(self, "Внимание!", "Файл \"NEWS.txt\" не был обнаружен в директории с исполняемым \
файлом. Для ознакомления со списком изменений вы можете обратиться к репозиторию на GitHub по ссылке выше.",
                                 QMessageBox.Ok)
        else:
            os.startfile("NEWS.txt")


class Settings(QWidget):
    """Окно "Настройки"."""

    def __init__(self):
        super(Settings, self).__init__()

        self.ui = Ui_Settings()
        self.ui.setupUi(self)

        self.setAttribute(Qt.WA_QuitOnClose, False)  # Закрываем окно, если оно последнее

        self.ui.pb_save.setObjectName("context-button")
        self.ui.pb_cancel.setObjectName("context-button")

        # ВРЕМЕННОЕ СКРЫТИЕ ПУНКТА "УМНОЕ ПРЕДЛОЖЕНИЕ"
        self.ui.l_8.hide()
        self.ui.cb_3.hide()
        self.ui.l_10.hide()
        self.ui.sb_4.hide()

        # Иконка приложения
        i_app = QIcon(QPixmap(":/icon.ico"))
        self.setWindowIcon(i_app)

        # Даю функционал кнопкам
        self.ui.pb_save.clicked.connect(self.save_settings)
        self.ui.pb_cancel.clicked.connect(self.close)
        self.ui.cb_1.clicked.connect(lambda x=self.ui.cb_1, y=self.ui.sb_3: self.check_cb_state(x, y))
        self.ui.cb_3.clicked.connect(lambda x=self.ui.cb_3, y=self.ui.sb_4: self.check_cb_state(x, y))

        # Актуализирую отображение сохранённых раннее настроек
        self.update_settings()

    @Slot()
    def save_settings(self):
        """Производит сохранение введённых значений в полях в файл настроек."""

        with open("settings.ini", "w") as file:
            file.write("default=" + str(self.ui.sb_1.value()) + "\n")
            file.write("repeat_amount=" + str(self.ui.sb_2.value()) + "\n")
            file.write("is_reset_progress=" + str(self.cb_int_state(self.ui.cb_2)) + "\n")
            file.write("is_mix_words=" + str(self.cb_int_state(self.ui.cb_4)) + "\n")
            file.write("is_smart_offer=" + str(self.cb_int_state(self.ui.cb_3)) + "\n")
            file.write("triggering_threshold=" + str(self.ui.sb_4.value()) + "\n")
            file.write("auto_next=" + str(self.cb_int_state(self.ui.cb_1)) + "\n")
            file.write("auto_time=" + str(self.ui.sb_3.value()) + "\n")

        self.close()

    @staticmethod
    def cb_int_state(checkbox):
        """Интерпретирует состояние checkbox из bool в int и возвращает его."""
        if checkbox.isChecked():
            return 1
        else:
            return 0

    def update_settings(self):
        """Просматривает "Settings.ini" и восстанавливает значения из него."""

        check_settings_existence()

        with open("settings.ini") as file:
            for param in file.readlines():
                param = param.rstrip("\n")
                if "default=" in param:
                    default_value = int(param.lstrip("default="))
                    self.ui.sb_1.setValue(default_value)
                elif "repeat_amount=" in param:
                    repeat_amount_value = int(param.lstrip("repeat_amount="))
                    self.ui.sb_2.setValue(repeat_amount_value)
                elif "is_reset_progress=" in param:
                    reset_progress_value = bool(int(param.lstrip("is_reset_progress=")))
                    self.ui.cb_2.setChecked(reset_progress_value)
                elif "is_mix_words=" in param:
                    mix_words_value = bool(int(param.lstrip("is_mix_words=")))
                    self.ui.cb_4.setChecked(mix_words_value)
                elif "is_smart_offer=" in param:
                    smart_offer_value = bool(int(param.lstrip("is_smart_offer=")))
                    self.ui.cb_3.setChecked(smart_offer_value)
                    self.check_cb_state(self.ui.cb_3, self.ui.sb_4)
                elif "triggering_threshold=" in param:
                    triggering_threshold_value = int(param.lstrip("triggering_threshold="))
                    self.ui.sb_4.setValue(triggering_threshold_value)
                elif "auto_next=" in param:
                    auto_next_value = bool(int(param.lstrip("auto_next=")))
                    self.ui.cb_1.setChecked(auto_next_value)
                    self.check_cb_state(self.ui.cb_1, self.ui.sb_3)
                elif "auto_time=" in param:
                    auto_time_value = int(param.lstrip("auto_time="))
                    self.ui.sb_3.setValue(auto_time_value)

    @staticmethod
    def check_cb_state(checkbox, spinbox):
        """Блокирует спин-бокс, если относящийся к нему чек-бокс выключен."""
        if not checkbox.isChecked():
            spinbox.setDisabled(True)
        else:
            spinbox.setDisabled(False)


class Training(QWidget):
    """Окно тренировки."""

    def __init__(self):
        super(Training, self).__init__()

        self.ui = Ui_Training()
        self.ui.setupUi(self)

        self.main_window = None
        self.results = None

        # Иконка приложения
        i_app = QIcon(QPixmap(":/icon.ico"))
        self.setWindowIcon(i_app)

        # Иконка кнопки "Назад в меню"
        global is_dark_mode
        if is_dark_mode:
            i_back = QIcon(QPixmap(":/icons/n_back.png"))
            self.ui.pb_back.setIcon(i_back)
        else:
            i_back = QIcon(QPixmap(":/icons/back.png"))
            self.ui.pb_back.setIcon(i_back)
            i_end_training = QIcon(QPixmap(":/icons/end_training.png"))
            self.ui.pb_end_training.setIcon(i_end_training)
            i_hard_word = QIcon(QPixmap(":/icons/hard_word.png"))
            self.ui.pb_make_wrong.setIcon(i_hard_word)
            i_delete_word = QIcon(QPixmap(":/icons/delete_word.png"))
            self.ui.pb_blacklisting.setIcon(i_delete_word)

        # Для стилей
        self.ui.l_header.setObjectName("training-header")
        self.ui.progressBar.setObjectName("training-prb")
        self.ui.pb_blacklisting.setObjectName("training-context-button")
        self.ui.pb_back.setObjectName("training-context-button")
        self.ui.pb_make_wrong.setObjectName("training-context-button")
        self.ui.pb_end_training.setObjectName("training-context-button")
        self.ui.l_example.setObjectName("example")
        self.ui.pb_next.setObjectName("next")

        # Функционал кнопок
        self.ui.pb_next.clicked.connect(self.next_question)
        self.ui.pb_back.clicked.connect(self.return_to_menu)
        self.ui.pb_end_training.clicked.connect(self.show_results)
        self.ui.pb_make_wrong.clicked.connect(self.make_wrong)
        self.ui.pb_blacklisting.clicked.connect(self.blacklisting)

        # Переменные
        self.a_word = ""  # Для текущего слова
        self.answer = 0  # Номер гласной-ответа
        self.current_word = 0  # Порядковый номер текущего слова
        self.last_word_id = self.current_word  # Порядковый номер предыдущего слова
        self.current_question = 1  # Для номера текущего вопроса
        self.current_repeat_w = -1  # Для номера повторяемого слова
        self.is_repeat_over = False  # Окончено ли повторение?

        self.completed_words = []  # Для хранения показанных слов
        self.word_progress = []  # Для хранения прогресса слов на повторении

        global questions_amount, is_repeat, repeats_amount, bad_words
        # Настройка прогресс-бара
        self.ui.progressBar.setMaximum(questions_amount)
        self.ui.progressBar.setValue(self.current_question)

        # ОПРЕДЕЛЕНИЕ ПАРАМЕТРОВ, ЕСЛИ КЛАСС БЫЛ ЗАПУЩЕН В РЕЖИМЕ ПОВТОРЕНИЯ
        if is_repeat:
            # Определение прогресса для каждого слова для повторения
            self.word_progress = [repeats_amount] * len(bad_words)
            self.whole_progress_value = 0

            # Определение максимального значения для прогресс-бара
            pbm = 0  # pbm - Progress Bar M... я не помню что значит 'm'. Впрочем, это не важно.
            for v in self.word_progress:
                pbm += v
                self.whole_progress_value = pbm
            self.ui.progressBar.setMaximum(pbm)
            self.ui.progressBar.setValue(1)

            self.ui.l_stats.hide()  # Скрываю текст со статистикой.
            self.ui.pb_end_training.setDisabled(True)
            self.ui.pb_make_wrong.setDisabled(True)
            self.ui.pb_blacklisting.setDisabled(True)

        self.question()  # Задаём первый вопрос / эта строка должна быть последней.

    def question(self):
        """Формирует вопрос для тренировки или повтора."""

        global is_repeat, bad_words

        # Возвращаем стили виджетов на место.
        if not is_repeat:
            self.ui.l_header.setText("Тренировка")
        else:
            self.ui.l_header.setText("Повторение")

        self.ui.l_header.setObjectName("training-header")
        self.ui.l_header.style().unpolish(self.ui.l_header)
        self.ui.l_header.style().polish(self.ui.l_header)

        self.ui.progressBar.setObjectName("training-prb")
        self.ui.progressBar.style().unpolish(self.ui.progressBar)
        self.ui.progressBar.style().polish(self.ui.progressBar)

        # Скрываем кнопку "далее"
        self.ui.pb_next.hide()

        # Если это первое слово - на кнопку "Определить пр. слово" нажать нельзя.
        if len(self.completed_words) <= 0:
            self.ui.pb_make_wrong.setDisabled(True)
        else:
            self.ui.pb_make_wrong.setDisabled(False)

        # -------------------------------------------------------------------

        selected_word = None  # Для хранения выбранного слова
        if not is_repeat:
            # Выбираем случайное слово и оформляем его
            selected_word = self.define_random_word()

            self.last_word_id = self.current_word
            self.current_word = selected_word

            self.a_word = self.define_word(selected_word)

            # while is_id_in_blacklist(self.a_word)

            self.update_stats()
        else:
            self.repeat()
            # Если повторение закончено, то закругляемся
            if self.is_repeat_over:
                self.clear_buttons()
                self.disable_buttons()
                self.ui.l_example.setText("")
                self.end_repeat()
                return 0
            self.a_word = self.define_word(bad_words[self.current_repeat_w])

        self.a_word = self.a_word.rstrip("\n")

        # Следующий отрезок кода находит и оформляет пример употребления, если он есть
        if "(" in self.a_word:
            # Отдельно храню слово и пример употребления
            example = ""
            word = ""
            reached_example = False
            for letter in self.a_word:
                # Если достигли пробела - значит, достигли примера
                if letter == " ":
                    reached_example = True
                # Если ещё не достигли примера - значит, это вопросное слово - записываем
                if not reached_example:
                    word += letter
                # Если это пример - записываем его
                if reached_example:
                    example += letter
            self.ui.l_example.setText(example)
            self.a_word = word
        else:
            self.ui.l_example.setText("")

        self.a_word = self.a_word.lower()

        # Определяем ответ на текущий вопрос
        if not is_repeat:
            self.answer = self.define_answer(selected_word)
        else:
            self.answer = self.define_answer(bad_words[self.current_repeat_w])

        # Так как я не смог сделать так, чтобы кнопки удалялись из layout'а после
        # ответа на вопрос и появлялись новые, мною было принято решение сделать
        # костыль. Суть такова: в первый раз создаётся необходимое количество
        # кнопок для каждой буквы в слове. В дальнейшем, если в слове больше букв,
        # чем кнопок, то создаются новые кнопки, если меньше, то лишние кнопки
        # будут скрыты.
        while self.ui.lo_training.count() < len(self.a_word):
            button = LetterButton()
            self.ui.lo_training.addWidget(button)

        vowel_number = 0  # Для отсчёта порядкового номера гласной
        x = 0
        while x < len(self.a_word):
            # Берём объект кнопки-буквы
            button = self.ui.lo_training.itemAt(x).widget()
            # Вставляем букву слова в кнопку
            button.setText(self.a_word[x])

            # Если текущая буква - гласная, увеличиваем счётчик.
            if self.a_word[x] in lower_vowels:
                vowel_number += 1
            # Если кнопка-буква является ответом - делаем её таковой.
            if vowel_number in self.answer and button.text() in lower_vowels:
                button.isAnswer = True
            # Добавляем соответствующие функции кнопкам в зависимости от их типа.
            if button.isAnswer and button.text() in lower_vowels:
                button.clicked.connect(self.correct)
            if not button.isAnswer and button.text() in lower_vowels:
                button.clicked.connect(self.incorrect)
            # Если кнопки-буквы - согласные, то отключаем их.
            if self.a_word[x] not in lower_vowels:
                button.setDisabled(True)

            x += 1

    def repeat(self):
        """Вызывается, когда включён режим повторения. Возвращает ID вопросного слова из списка с ошибками проходясь
по ним по очереди."""

        global bad_words, is_mix_words

        # Если все слова повторены - собираемся выходить из повторения
        if self.word_progress.count(0) == len(self.word_progress):
            self.is_repeat_over = True
            return 0

        # Ищем слово, которое ещё нужно повторить
        while True:
            if is_mix_words:
                # Если включена опция - вытаскиваем случайное слово
                self.current_repeat_w = random.randint(0, len(bad_words))
            else:
                # Иначе, смотрим слова по порядку...
                self.current_repeat_w += 1
            # ...и проверяем, чтобы мы не вышли за границы дозволенного
            if self.current_repeat_w >= len(bad_words):
                self.current_repeat_w = 0
            # Если мы наткнулись на повторённое слово, то ищем следующее не повторённое
            if self.word_progress[self.current_repeat_w] == 0:
                continue
            else:
                break

    def end_repeat(self):
        """Завершает повторение, если оно было завершено."""
        self.ui.l_header.setText("Повторение окончено!")
        self.ui.pb_next.clicked.disconnect(self.next_question)
        self.ui.pb_next.clicked.connect(self.return_to_menu)
        self.ui.pb_next.setText("Вернуться в меню")
        self.ui.pb_next.show()

    def change_progress(self):
        """Меняет значение в Progress Bar."""
        global is_repeat

        # Не в режиме повторения...
        if not is_repeat:
            # Увеличиваем значение номера текущего вопроса и меняем значение прогресс-бара
            self.current_question += 1
            self.ui.progressBar.setValue(self.current_question)
        else:
            # Иначе просто меняем прогресс в режиме повторения
            pbm = 0
            for v in self.word_progress:
                pbm += v
            self.ui.progressBar.setValue(self.whole_progress_value - pbm + 1)

    def update_stats(self):
        """Обновление текста со статистикой."""
        global questions_amount, bad_words, score

        incorrect_amount = len(bad_words)
        whole_amount = questions_amount - len(self.completed_words) + 1
        correct_amount = score

        the_text = "<span style='font-weight: bold;'>" + \
                   "<span style='color: red;'>" + \
                   str(incorrect_amount) + \
                   "</span>" + \
                   "    |   " + str(whole_amount) + \
                   "    |   <span style='color: green;'>" + str(correct_amount) + \
                   "</span>" + \
                   "</span>"

        self.ui.l_stats.setText(the_text)

    def show_buttons(self):
        """Показывает кнопки в зависимости от количества букв в текущем слове."""
        x = 0
        while x < len(self.a_word):
            button = self.ui.lo_training.itemAt(x).widget()
            button.show()
            x += 1

    def clear_buttons(self):
        """Очищает кнопки: текст, параметры; делаем их доступными к нажатию,
затем скрывает их."""

        button_amount = self.ui.lo_training.count()

        x = 0
        while x < button_amount:
            button = self.ui.lo_training.itemAt(x).widget()
            button.isAnswer = False
            button.setText("")
            button.setDisabled(False)
            button.hide()

            button.setObjectName("training-button")
            button.style().unpolish(button)
            button.style().polish(button)

            x += 1

    def designalize_buttons(self):
        """Отключает сигналы от всех кнопок."""
        button_amount = self.ui.lo_training.count()

        x = 0
        while x < button_amount:
            button = self.ui.lo_training.itemAt(x).widget()
            if button.isAnswer and button.text() in lower_vowels:
                button.clicked.disconnect(self.correct)
            elif not button.isAnswer and button.text() in lower_vowels:
                button.clicked.disconnect(self.incorrect)

            x += 1

    def disable_buttons(self):
        """Делает кнопки неактивными. Используется только по окончании повторения."""
        x = 0
        while x < self.ui.lo_training.count():
            self.ui.lo_training.itemAt(x).widget().setDisabled(True)
            x += 1

    @Slot()
    def next_question(self):
        """Производит переход к следующему вопросу."""
        self.clear_buttons()

        global is_repeat

        # НЕ в режиме повторения...
        if not is_repeat:
            # Если мы ещё не ответили на всё количество вопросов...
            if self.current_question < questions_amount:
                # Я думаю, менять порядок функций здесь не стоит. А то не дай бог...
                self.question()  # Задаём вопрос
                self.change_progress()  # Меняем прогресс
                self.show_buttons()  # Показываем кнопки
            # Если ответили, то показываем окно результатов
            else:
                self.show_results()
        # В режиме повторения, если он ещё не закончен, действуем почти аналогично
        else:
            if not self.is_repeat_over:
                self.question()
                self.change_progress()
                self.show_buttons()

    @Slot()
    def show_correct(self):
        """Визуально демонстрирует пользователю правильный ответ на вопрос."""

        x = 0
        while x < len(self.a_word):
            # Берём объект кнопки-буквы
            button = self.ui.lo_training.itemAt(x).widget()

            if button.isAnswer:
                button.setObjectName("training-button-corr")
                button.style().unpolish(button)
                button.style().polish(button)

            x += 1

    @Slot()
    def correct(self):
        """Вызывается, если на вопрос был дан верный ответ."""

        # Отключение происходит сразу же, чтобы пользователь больше не нажимал
        # на кнопки с последствиями
        self.designalize_buttons()

        global next_question_delay, is_auto_next, is_repeat, score

        # Меняем стиль виджетов
        self.ui.l_header.setText("Правильно!")

        self.ui.l_header.setObjectName("training-header-corr")
        self.ui.l_header.style().unpolish(self.ui.l_header)
        self.ui.l_header.style().polish(self.ui.l_header)

        self.ui.progressBar.setObjectName("training-prb-corr")
        self.ui.progressBar.style().unpolish(self.ui.progressBar)
        self.ui.progressBar.style().polish(self.ui.progressBar)

        score += 1
        self.update_stats()

        # Показываем правильный ответ
        self.show_correct()

        # Если мы в режиме повторения, то меняем прогресс для данного слова
        if is_repeat:
            self.word_progress[self.current_repeat_w] -= 1

        # Срабатывает, если включена опция автоматического перехода
        if is_auto_next:
            # Создаём таймер, по истечению которого перейдём к следующему вопросу.
            a_timer = QTimer()
            a_timer.singleShot(next_question_delay, self.next_question)
            a_timer.start()
        # Иначе демонстрируем кнопку
        else:
            self.ui.pb_next.show()

    @Slot()
    def incorrect(self):
        """Вызывается, если на вопрос был дан неверный ответ."""

        global next_question_delay, bad_words, is_auto_next, is_repeat, is_reset_progress, repeats_amount, \
            is_smart_offer

        # Отключение происходит сразу же, чтобы пользователь больше не нажимал
        # на кнопки с последствиями
        self.designalize_buttons()

        # НЕ в режиме повторения добавляем ошибочное слово в список для дальнейшего повторения
        if not is_repeat:
            bad_words.append(self.current_word)

            if is_smart_offer:
                self.smart_add()
        # В режиме повторения, если включена опция, сбрасываем прогресс для слова,
        # если ответ на него неверен
        elif is_repeat and is_reset_progress:
            self.word_progress[self.current_repeat_w] = repeats_amount

        # Меняем стиль виджетов
        self.ui.l_header.setText("Неправильно!")

        self.ui.l_header.setObjectName("training-header-incorr")
        self.ui.l_header.style().unpolish(self.ui.l_header)
        self.ui.l_header.style().polish(self.ui.l_header)

        self.ui.progressBar.setObjectName("training-prb-incorr")
        self.ui.progressBar.style().unpolish(self.ui.progressBar)
        self.ui.progressBar.style().polish(self.ui.progressBar)

        # Показываем правильный ответ
        self.show_correct()

        self.update_stats()

        # Аналогично, как и в correct()
        if is_auto_next:
            # Создаём таймер, по истечению которого перейдём к следующему вопросу.
            a_timer = QTimer()
            a_timer.singleShot(next_question_delay, self.next_question)
            a_timer.start()
        else:
            self.ui.pb_next.show()

    @Slot()
    def return_to_menu(self):
        """Возвращение в главное меню"""
        global main_window
        clear_globals()
        main_window = MainWindow()
        main_window.show()
        self.close()

    @Slot()
    def make_wrong(self):
        """Реализация кнопки "отметить предыдущее слово как неверное"."""
        global bad_words, score
        if self.last_word_id not in bad_words:
            bad_words.append(self.last_word_id)
            score -= 1
            self.update_stats()

    @Slot()
    def blacklisting(self):
        """Реализация кнопки 'добавить в чёрный список'."""

        # Создаём чёрный список, если его ещё нет
        if not os.path.isfile("blacklist.txt"):
            with open("blacklist.txt", "w") as f:
                pass

        with open("blacklist.txt", "r") as file:
            content = file.read()

        with open("blacklist.txt", "a") as file:
            if self.current_word not in content:
                file.write(str(self.current_word) + "\n")

    @Slot()
    def show_results(self):
        """Демонстрация окна с результатами."""
        self.results = Results(self.completed_words)
        self.results.show()
        self.close()

    # def smart_add(self):
    #     """Работа с умным предложением слов."""
    #
    #     if not os.path.isfile("hard_words.txt"):
    #         with open("hard_words.txt", "w") as file:
    #             pass
    #
    #     # СОХРАНЯЕМ ТЕКУЩЕЕ СОДЕРЖАНИЕ ФАЙЛА
    #     with open("hard_words.txt") as file:
    #         file_backup = file.readlines()
    #         print(file_backup)
    #
    #     # ПРОВЕРЯЕМ НАЛИЧИЕ СЛОВА В ФАЙЛЕ
    #     target = self.a_word
    #     print("Target", target)
    #     line = 1
    #     while line <= len(file_backup):
    #         print("Line:", line)
    #
    #         # Оформляем текущее слово в файле для обработки
    #         destination = ""
    #         raw_destination = file_backup[line-1]
    #         for letter in raw_destination:
    #             if letter == ":":
    #                 print("Destination:", destination)
    #                 break
    #             else:
    #                 destination += letter
    #
    #         if target == destination:
    #             print("Слово уже есть в файле!")
    #             break
    #         else:
    #             line += 1
    #     else:
    #         with open("hard_words.txt", "a") as file:
    #             file.write(self.a_word + ": 1\n")

    def define_word(self, line):
        """Ищет слово в words.txt, которое нужно загадать, на основе переданного числа (line)."""

        check_words_existence(self)

        with open("words.txt") as file:
            the_word = None
            x = 1
            while x <= line:
                the_word = file.readline()
                x += 1

            return the_word

    def define_random_word(self):
        """Определяет и возвращает случайный номер слова для вопроса, если его ещё не было."""

        check_words_existence(self)

        with open("words.txt", "r") as file:

            # Узнаём количество строк в words.txt
            amount_of_lines = len(file.readlines())
            while True:
                # Генерируем число, которое равносильно номеру строки в файле words.txt
                a_number = random.randint(1, amount_of_lines)
                if a_number not in self.completed_words:
                    self.completed_words.append(a_number)
                    break

        return a_number

    def define_answer(self, number):
        """Ищет в answers ответ на вопрос и возвращает его."""

        # Если был удалён файл answers
        if not os.path.isfile("answers"):
            find_answers(self)

        with open("answers") as file:
            the_answer = None
            x = 1
            # Пока не дошли до ответа для загаданного слова...
            while x <= number:
                # Читаем строки и увеличиваем счётчик
                the_answer = file.readline()
                x += 1

            # Отрезаем перевод строки
            the_answer = the_answer.rstrip("\n")

            # Переменная отвечает за то, множественный ли ответ для слова или нет
            is_multiple_answer = False
            # Определяем, множественный ли ответ, по наличию "/" в нём
            for y in the_answer:
                if y == "/":
                    is_multiple_answer = True
                    break

            # Если ответ множественный...
            if is_multiple_answer:
                # Ищем все числа-ответы, перебирая строку с ответом исключая "/"
                the_multiple_answer = []
                for y in the_answer:
                    if y != "/":
                        # Записываем возможные ответы в переменную-список в типе int
                        the_multiple_answer.append(int(y))
                # Возвращаем список с ответами
                return the_multiple_answer
            # Если ответ является единичным, то делаем его списком
            else:
                the_answer = int(the_answer)
                the_answer = [the_answer]
                # Возвращаем единичный ответ в виде списка
                return the_answer


class Results(QWidget):
    """Окно результатов."""

    def __init__(self, completed_words):
        super(Results, self).__init__()

        self.ui = Ui_Results()
        self.ui.setupUi(self)

        # Иконка приложения
        i_app = QIcon(QPixmap(":/icon.ico"))
        self.setWindowIcon(i_app)

        # Для установки стилей
        self.ui.l_header.setObjectName("header")
        self.ui.l_grade.setObjectName("grade")
        self.ui.l_comment.setObjectName("comment")
        self.ui.pb_menu.setObjectName("context-button")
        self.ui.pb_again.setObjectName("context-button")
        self.ui.pb_exit.setObjectName("context-button")
        self.ui.pb_cont.setObjectName("context-button")

        # Функционал кнопок
        self.ui.pb_exit.clicked.connect(self.exit)
        self.ui.pb_menu.clicked.connect(self.menu)
        self.ui.pb_again.clicked.connect(self.again)
        self.ui.pb_cont.clicked.connect(self.repeat)

        self.completed_words = completed_words

        # Скрытие кнопки "повторение", если были ошибки в словах
        global bad_words
        if len(bad_words) <= 0:
            self.ui.pb_cont.hide()

        self.results()

    @staticmethod
    def exit():
        """Выход из приложения."""
        QCoreApplication.instance().quit()

    @Slot()
    def again(self):
        """Начать тренировку заново."""
        global training_window
        self.clear()
        training_window = None
        training_window = Training()
        training_window.show()
        self.close()
        # training_window.update_stats()

    @Slot()
    def menu(self):
        """Вернуться в главное меню (главное окно)."""
        global main_window
        clear_globals()
        main_window = MainWindow()
        main_window.show()
        self.close()

    @Slot()
    def repeat(self):
        """Включение режима повторения."""
        global is_repeat, training_window
        is_repeat = True
        training_window = None
        training_window = Training()
        training_window.show()
        self.close()

    @staticmethod
    def clear():
        """Очистка некоторых глобальных переменных."""
        global bad_words, score
        bad_words = []
        score = 0

    def results(self):
        """Отображает результат тренировки и даёт соответствующий комментарий."""

        global questions_amount, bad_words, score

        one_percent = questions_amount / 100  # Определили один процент от общего числа вопросов

        first_grade = questions_amount  # Ответили на все вопросы
        second_grade = one_percent * 75  # Ответили на 75% вопросов
        third_grade = one_percent * 50  # Ответили на 50% вопросов
        fourth_grade = one_percent * 25  # Ответили на 25% вопросов
        fifth_grade = 0  # Не ответили ни на один вопрос

        grade_text = str(score) + " правильных ответов из " + str(len(self.completed_words))
        self.ui.l_grade.setText(grade_text)

        # Ответили на все вопросы
        if score >= first_grade:
            self.ui.l_comment.setText("Прекрасный результат! Вы великолепны!")

        # Ответили на 99%-75% вопросов
        elif first_grade > score >= second_grade:
            self.ui.l_comment.setText("Вы весьма неплохо справляетесь! В следующий раз у вас получится \
ответить на все вопросы!")

        # Ответили на 74%-50%
        elif second_grade > score >= third_grade:
            self.ui.l_comment.setText("Хорошо потрудились! Продолжайте в том же духе!")

        # На 49%-25%
        elif third_grade > score >= fourth_grade:
            self.ui.l_comment.setText("В целом - неплохо, но есть куда стремиться!")

        # 24%-0%
        elif fourth_grade > score >= fifth_grade:
            self.ui.l_comment.setText("Результат не впечатляет... Не расстраивайтесь! Отдохните и \
попробуйте ещё раз!")


class LetterButton(QPushButton):
    """Класс кнопки-буквы."""

    def __init__(self):
        super(LetterButton, self).__init__()

        self.setObjectName("training-button")
        self.setMinimumSize(50, 50)
        self.setMaximumSize(50, 50)

        self.isAnswer = False


def is_id_in_blacklist(target):
    try:
        with open("blacklist.txt", "r") as file:
            content = file.readlines()
            for line in content:
                if target.rstrip() == line:
                    return True
            else:
                return False
    except FileNotFoundError:
        print("Файла 'blacklist.txt' не существует.")


def find_answers(calling_window):
    """Вызывается при всяком запуске тренажёра и нажатии кнопки "Начать".
Просматривает файл words.txt и на основе заглавных букв в словах составляет
файл с ответами - answers."""

    check_words_existence(calling_window)

    ans = open("answers", "w")
    file = open("words.txt")

    while True:
        # Читаем строку в файле
        a_line = file.readline()
        # Отрезаем окончание
        a_line = a_line.rstrip("\n")

        # Прерываем цикл, если встречается пустая строка - это значит весь файл уже прочитан
        if not a_line:
            break

        # Иначе исследуем каждый символ в прочитанной строке, ведь строка - это одно слово.
        amount_of_vowels = 0
        # Переменная отвечает за то, была ли уже найдена заглавная буква или ещё нет
        found_percussive_vowel = False

        for x in a_line:
            # Если это строчная гласная, то просто увеличиваем количество гласных для этого слова.
            if x in lower_vowels:
                amount_of_vowels += 1

            # Если заглавная (ударная) гласная, то не только увеличиваем их количество, но
            # и записываем эту гласную как ответ к слову в файл answers,
            # а если есть и другие ударные гласные, то через "/" записываем и их
            elif x in upper_vowels:
                amount_of_vowels += 1
                if not found_percussive_vowel:
                    found_percussive_vowel = True
                    ans.write(str(amount_of_vowels))
                elif found_percussive_vowel:
                    ans.write("/")
                    ans.write(str(amount_of_vowels))

        ans.write("\n")  # Перевод строки после записи ответа для слова

    file.close()
    ans.close()


def check_settings_existence():
    """Проверяет наличие settings.ini и если не обнаруживает файл, то создаёт его."""

    if not os.path.isfile("settings.ini"):
        filler = "default=10\nrepeat_amount=3\nis_reset_progress=0\nis_mix_words=0\nis_smart_offer=1\n" + \
                 "triggering_threshold=2\nauto_next=1\nauto_time=1000\n"
        with open("settings.ini", "w") as file:
            file.write(filler)


def check_words_existence(calling_window):
    """Если не был обнаружен words.txt, то создаём его и заполняем несколькими
словами и сообщаем о ненахождении."""

    if not os.path.isfile("words.txt"):
        QMessageBox.question(calling_window, "Внимание!", "Файл \"words.txt\" не был обнаружен в директории с исполняемым\
                                                              файлом. Он будет создан и заполнен несколькими словами. \
                                                              Пожалуйста, поместите исходный файл \"words.txt\" или \
                                                              настройте его самостоятельно в соответствии с инструкцией в \
                                                              \"README.txt\".",
                             QMessageBox.Ok)

        filler = "бАнты\nтОрты\nшАрфы\nпОрты\nсрЕдства\nИксы\nкрАны\nкОнусы\nлЕкторы\nпОручни"

        with open("words.txt", "w") as file:
            file.write(filler)


def extract_settings():
    """Сохраняет значения из файла настроек в соответствующие глобальные переменные."""
    global default_amount, next_question_delay, repeats_amount, is_auto_next, \
        is_reset_progress, is_mix_words, is_smart_offer, triggering_threshold

    check_settings_existence()
    with open("settings.ini") as file:

        for param in file.readlines():
            if "default=" in param:
                default_amount = int(param.lstrip("default="))
            elif "repeat_amount=" in param:
                repeats_amount = int(param.lstrip("repeat_amount="))
            elif "auto_next=" in param:
                is_auto_next = bool(int(param.lstrip("auto_next=")))
            elif "auto_time=" in param:
                next_question_delay = int(param.lstrip("auto_time="))
            elif "is_reset_progress=" in param:
                is_reset_progress = bool(int(param.lstrip("is_reset_progress=")))
            elif "is_mix_words=" in param:
                is_mix_words = bool(int(param.lstrip("is_mix_words=")))
            elif "is_smart_offer=" in param:
                is_smart_offer = bool(int(param.lstrip("is_smart_offer=")))
            # elif "triggering_threshold=" in param:
            #     triggering_threshold = int(param.lstrip("triggering_threshold="))


def clear_globals():
    """Очищает глобальные переменные, приводя их к значениям по умолчанию (исключая глобальные переменные)."""

    global main_window, training_window, questions_amount, bad_words, is_repeat, score
    main_window = None
    training_window = None
    questions_amount = 0
    bad_words = []
    is_repeat = False
    score = 0


# НАЧАЛО ПРОГРАММЫ
if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()

    with open("style.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    sys.exit(app.exec_())
