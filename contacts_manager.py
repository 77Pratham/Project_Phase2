import pandas as pd

class ContactsManager:
    def __init__(self, filepath="contacts.csv"):
        self.filepath = filepath
        self.df = pd.read_csv(filepath)

    def get_email(self, name):
        row = self.df[self.df['name'].str.lower() == name.lower()]
        if not row.empty:
            return row.iloc[0]['email']
        return None

    def get_group_emails(self, group_name):
        rows = self.df[self.df['group_name'].str.lower() == group_name.lower()]
        return rows['email'].tolist()

    def get_all_students(self):
        rows = self.df[self.df['role'] == "student"]
        return rows['email'].tolist()

    def get_all_staff(self):
        rows = self.df[self.df['role'] == "staff"]
        return rows['email'].tolist()
