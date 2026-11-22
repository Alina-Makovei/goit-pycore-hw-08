
import pickle
from pathlib import Path
from collections import UserDict
from datetime import datetime, date, timedelta


# Шлях до файлу для збереження адресної книги
FILE_PATH = Path(__file__).parent / "addressbook.pkl"



# Класи для роботи з контактами


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Номер телефону має містити рівно 10 цифр.")

        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y")

            if birthday.strftime("%d.%m.%Y") != value:
                raise ValueError

            super().__init__(birthday)

        except (ValueError, TypeError):
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        found_phone = self.find_phone(phone)

        if found_phone is None:
            raise ValueError("Телефон не знайдено.")

        self.phones.remove(found_phone)

    def edit_phone(self, old_phone, new_phone):
        found_phone = self.find_phone(old_phone)

        if found_phone is None:
            raise ValueError("Телефон не знайдено.")

        new_phone = Phone(new_phone)
        index = self.phones.index(found_phone)
        self.phones[index] = new_phone

    def find_phone(self, phone):
        for saved_phone in self.phones:
            if saved_phone.value == phone:
                return saved_phone

        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(phone.value for phone in self.phones)
        return f"Contact name: {self.name.value}, phones: {phones}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = date.today()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday = record.birthday.value.date()

            try:
                birthday_this_year = birthday.replace(year=today.year)
            except ValueError:
                birthday_this_year = date(today.year, 2, 28)

            if birthday_this_year < today:
                try:
                    birthday_this_year = birthday.replace(year=today.year + 1)
                except ValueError:
                    birthday_this_year = date(today.year + 1, 2, 28)

            if 0 <= (birthday_this_year - today).days <= 7:
                congratulation_date = birthday_this_year

                if congratulation_date.weekday() == 5:
                    congratulation_date += timedelta(days=2)
                elif congratulation_date.weekday() == 6:
                    congratulation_date += timedelta(days=1)

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congratulation_date.strftime("%d.%m.%Y")
                })

        return upcoming_birthdays



# Збереження та завантаження даних


def save_data(book, filename=FILE_PATH):
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename=FILE_PATH):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)

    except FileNotFoundError:
        return AddressBook()



# Обробка помилок


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except KeyError:
            return "Contact not found."

        except ValueError as error:
            return str(error) or "Give me name and phone please."

        except IndexError:
            return "Enter user name."

    return inner



# Парсинг введеної команди


def parse_input(user_input):
    parts = user_input.split()

    if not parts:
        return "", []

    cmd, *args = parts
    cmd = cmd.lower()

    return cmd, args



# Обробники команд


@input_error
def add_contact(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Give me name and phone please.")

    name, phone, *_ = args

    record = book.find(name)
    message = "Contact updated."

    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."

    record.add_phone(phone)

    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) < 3:
        raise ValueError("Give me name, old phone and new phone please.")

    name, old_phone, new_phone, *_ = args

    record = book.find(name)

    if record is None:
        raise KeyError

    record.edit_phone(old_phone, new_phone)

    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    if not args:
        raise ValueError("Enter user name.")

    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    if not record.phones:
        return "No phone numbers saved."

    return "; ".join(phone.value for phone in record.phones)


@input_error
def show_all(args, book: AddressBook):
    if args:
        raise ValueError("The 'all' command does not need arguments.")

    if not book.data:
        return "No contacts saved."

    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) < 2:
        raise ValueError("Give me name and birthday please.")

    name, birthday, *_ = args

    record = book.find(name)

    if record is None:
        raise KeyError

    record.add_birthday(birthday)

    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    if not args:
        raise ValueError("Enter user name.")

    name = args[0]
    record = book.find(name)

    if record is None:
        raise KeyError

    if record.birthday is None:
        return "Birthday is not set."

    return record.birthday.value.strftime("%d.%m.%Y")


@input_error
def birthdays(args, book: AddressBook):
    if args:
        raise ValueError("The 'birthdays' command does not need arguments.")

    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No birthdays in the next 7 days."

    result = []

    for user in upcoming:
        result.append(
            f"{user['name']}: {user['congratulation_date']}"
        )

    return "\n".join(result)



# Головна функція бота


def main():
    book = load_data()

    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello" and not args:
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
