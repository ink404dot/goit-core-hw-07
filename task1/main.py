from collections import UserDict
from typing import Optional, List, Dict, Tuple, Callable
from datetime import datetime, timedelta


class PhoneValidationError(Exception):
    def __init__(self, message: str =
                 "The phone number must be 10 characters long.") -> None:
        self.message = message
        super().__init__(self.message)


class NameValidationError(Exception):
    def __init__(self, message: str =
                 "Length must be at least 1 character in string format") -> None:
        self.message = message
        super().__init__(self.message)


class BirthdayValidationError(Exception):
    def __init__(self, message: str =
                 "Invalid date format. Use DD.MM.YYYY") -> None:
        self.message = message
        super().__init__(self.message)


class ItemNotFoundError(Exception):
    def __init__(self, item: str =
                 "") -> None:
        self.message = "Not found " + item
        super().__init__(self.message)


class Field:
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Name(Field):
    def __init__(self, value: str):
        if self.validate(value):
            super().__init__(value)
        else:
            raise NameValidationError()

    @staticmethod
    def validate(value: str) -> bool:
        return isinstance(value, str) and len(value) > 1


class Phone(Field):
    def __init__(self, value: str):
        if self.validate(value):
            super().__init__(value)
        else:
            raise PhoneValidationError()

    @staticmethod
    def validate(value: str) -> bool:
        return len(value) == 10 and value.isdigit()


class Birthday(Field):
    def __init__(self, value: str):
        if self.str_to_datetime(value):
            super().__init__(value)
        else:
            raise BirthdayValidationError()

    @staticmethod
    def str_to_datetime(value: str) -> bool:
        return bool(datetime.strptime(value, "%d.%m.%Y"))


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, string):
        self.birthday = Birthday(string)

    def add_phone(self, value: str) -> None:
        self.phones.append(Phone(value))

    def remove_phone(self, value: str) -> None:
        for phone in self.phones:
            if phone.value == value:
                self.phones.remove(phone)
                return
        raise ItemNotFoundError(value)

    def find_phone(self, value: str) -> Optional[Phone]:
        matching_phones = [
            phone for phone in self.phones if phone.value == value]
        return matching_phones[0] if matching_phones else None

    def edit_phone(self, old_value: str, new_value: str) -> None:
        if Phone.validate(new_value):
            self.remove_phone(old_value)
            self.add_phone(new_value)
        else:
            raise PhoneValidationError()

    def __str__(self) -> str:
        return f"Contact name: {self.name.value}, phones: {
            '; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    def get_upcoming_birthdays(self) -> List[Dict[str, datetime]]:
        today = datetime.now()
        today_plus_seven_days = today + timedelta(days=7)
        upcoming_birthdays = []

        for record in self.data.values():
            greeting_date = None  # Initialize greeting_date
            if record.birthday:
                birthday_this_year = datetime.strptime(
                    str(record.birthday), "%d.%m.%Y").replace(year=today.year)

                if today <= birthday_this_year <= today_plus_seven_days:
                    greeting_date = birthday_this_year

                elif birthday_this_year < today:
                    birthday_next_year = birthday_this_year.replace(
                        year=today.year + 1)
                    if birthday_next_year <= today_plus_seven_days:
                        greeting_date = birthday_next_year

                if greeting_date and greeting_date.weekday() >= 5:
                    greeting_date += timedelta(days=(7 -
                                               greeting_date.weekday()))

                if greeting_date:
                    upcoming_birthdays.append(
                        {"name": str(record.name),
                            "birthday": greeting_date.strftime('%d.%m.%Y')}
                    )

        return upcoming_birthdays if upcoming_birthdays else 'There are no upcoming birthdays yet'

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str) -> None:
        if name in self.data:
            del self.data[name]
        else:
            raise ItemNotFoundError(name)

    def __str__(self) -> str:
        return '\n'.join(str(record) for record in self.data.values())


def input_error(func: Callable) -> Callable:
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return "Give right arguments, please.\n" +\
                "\tDate format: string, use DD.MM.YYYY\n" +\
                "\tName format: string, length more than 1\n" +\
                "\tPhone format: all characters in a string are digits, length equal 10"
        except KeyError:
            return "This contact does not exist."
        except IndexError or TypeError:
            return "Not enough arguments."
        except PhoneValidationError as e:
            return e
        except NameValidationError as e:
            return e
        except BirthdayValidationError as e:
            return e
        except ItemNotFoundError as e:
            return e
        except Exception as e:
            return e
    return inner


def parse_input(user_input: str) -> Tuple[str, List]:
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args


@input_error
def change_contact(args: List[str], book: AddressBook) -> str:
    name = args[0]
    old_phone, new_phone = args[1], args[2]

    record = book.find(name)
    if record is None:
        return f'Contact {name} not found.'

    record.edit_phone(old_phone, new_phone)
    return f'Contact {name} updated successfully.'


@input_error
def add_contact(args, book: AddressBook):
    name, phone, = args[0], args[1]
    record = book.find(name)
    if record:
        record.add_phone(phone)
        return "Contact updated."
    else:
        record = Record(name)
        book.add_record(record)
        record.add_phone(phone)
        book.add_record(record) 
    return "Contact added."


@input_error
def add_birthday(args: List[str], book: AddressBook) -> str:
    name, birthday = args[0], args[1]
    record = book.find(name)
    if record is None:
        return f'Contact {name} not found.'
    record.add_birthday(birthday)
    return "Contact updated."


@input_error
def show_birthday(args: List[str], book: AddressBook) -> str:
    name = args[0]
    record = book.find(name)
    if record is None:
        return f'Birthday for {name} not found.'
    return record.birthday if record.birthday else 'Birthday is None'


@input_error
def show_phone(args: List[str], book: AddressBook) -> list:
    name = args[0]
    record = book.find(name)
    if record is None:
        return f'Contact {name} not found.'
    return ', '.join(
        [str(phone) for phone in record.phones]
    ) if record.phones else 'No phones found.'


@input_error
def show_all(book: AddressBook) -> str:
    if not book:
        return "No contacts."

    header = f'{"name":^12}|{"birthday":^12}|{"phones":^12}'
    rows = []

    for name, record in book.data.items():
        birthday_str = str(record.birthday) if record.birthday else ' '
        phones_str = ", ".join(str(phone) for phone in record.phones)
        row = f'{name:^12}|{birthday_str:^12}|{phones_str:^12}'
        rows.append(row)

    return header + '\n' + '\n'.join(rows)


@input_error
def birthdays(book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if isinstance(upcoming_birthdays, str):  # If there's a message instead of a list
        return upcoming_birthdays
    else:
        return '\n'.join([f"{entry['name']} : {entry['birthday']}" for entry in upcoming_birthdays])


def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        match command:
            case "close" | "exit":
                print("Good bye!")
                break
            case "hello":
                print("How can I help you?")
            case "add":
                print(add_contact(args, book))
            case "change":
                print(change_contact(args, book))
            case "phone":
                print(show_phone(args, book))
            case "all":
                print(show_all(book))
            case "birthdays":
                print(birthdays(book))
            case "add-birthday":
                print(add_birthday(args, book))
            case "show-birthday":
                print(show_birthday(args, book))
            case _:
                print("Invalid command.")


# Приклад використання
if __name__ == "__main__":
    main()
