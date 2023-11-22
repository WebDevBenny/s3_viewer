import os
import configparser
import sys
from tkinter import (
    PhotoImage,
    ttk,
    Tk,
    Listbox,
    Text,
    Checkbutton,
    BooleanVar,
    Label,
    Entry,
    Button,
    Menu,
)
import boto3
import logging


class S3Configurator:
    def __init__(self):
        self.root = Tk()
        self.root.title("S3 Viewer Konfiguration")
        self.root.geometry("400x300")

        self.endpoint_url_entry = self.s3_options_fields("Endpoint URL", 50, False)
        self.access_key_id_entry = self.s3_options_fields("Access Key ID", 50, False)
        self.secret_access_key_entry = self.s3_options_fields(
            "Secret Access Key", 50, True
        )

        save_button = Button(
            self.root, text="Änderungen speichern", command=self.save_config
        )
        save_button.pack(side="bottom")
        logging.basicConfig(
            filename="Error.log",
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        self.create_context_menu()

    def create_context_menu(self):
        # Create a context menu
        self.context_menu = Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Option 1", command=self.option1)
        self.context_menu.add_command(label="Option 2", command=self.option2)

    def option1(self):
        # Code for option 1
        pass

    def option2(self):
        # Code for option 2
        pass

    def setup_error_log():
        # Configure logging to write error logs to a file named 'Error.log'
        logging.basicConfig(
            filename="Error.log",
            level=logging.ERROR,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )

    def log_error(error_message):
        # Log the error message
        logging.error(error_message)

    def s3_options_fields(self, text, width, secret):
        frame = self.root
        label = Label(frame, text=text)
        label.pack(side="top")
        label.pack(padx=5, pady=5)
        label.config(font=("Courier", 12))
        if secret:
            entry = Entry(frame, width=width, show="*")
            entry.pack(side="top")
        else:
            entry = Entry(frame, width=width)
            entry.pack(side="top")
        return entry

    def s3_options(self, frame, text, width, config, secret):
        frame = self.settings_frame
        label = Label(frame, text=text)
        label.pack(side="top")
        label.pack(padx=5, pady=5)
        label.config(font=("Courier", 12))
        if secret:
            entry = Entry(frame, width=width, show="*")
            entry.insert(0, config)
            entry.pack(side="top")
        else:
            entry = Entry(frame, width=width)
            entry.insert(0, config)
            entry.pack(side="top")
        return entry

    def save_config(self):
        config = configparser.ConfigParser()
        config["S3"] = {
            "Endpoint URL": self.endpoint_url_entry.get(),
            "Access Key ID": self.access_key_id_entry.get(),
            "Secret Access Key": self.secret_access_key_entry.get(),
        }
        with open("config.ini", "w") as configfile:
            config.write(configfile)
        self.root.destroy()
        os.execv(sys.executable, ["python"] + sys.argv)

    def s3_client(self):
        try:
            self.config = configparser.ConfigParser()
            self.config.read("config.ini")
            s3_client = boto3.client(
                "s3",
                endpoint_url=self.config["S3"]["Endpoint URL"],
                aws_access_key_id=self.config["S3"]["Access Key ID"],
                aws_secret_access_key=self.config["S3"]["Secret Access Key"],
                config=boto3.session.Config(signature_version="s3v4"),
            )
        except configparser.Error as e:
            logging.error(
                f"Beim Lesen der Konfigurationsdatei ist ein Fehler aufgetreten: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"Beim Erstellen des S3-Clients ist ein Fehler aufgetreten: {e}"
            )
            return None

        return s3_client

    def s3_resource(self):
        try:
            self.config = configparser.ConfigParser()
            self.config.read("config.ini")
            s3 = boto3.resource(
                "s3",
                endpoint_url=self.config["S3"]["Endpoint URL"],
                aws_access_key_id=self.config["S3"]["Access Key ID"],
                aws_secret_access_key=self.config["S3"]["Secret Access Key"],
                config=boto3.session.Config(signature_version="s3v4"),
            )
        except configparser.Error as e:
            logging.error(
                f"Beim Lesen der Konfigurationsdatei ist ein Fehler aufgetreten: {e}"
            )
            return None
        except Exception as e:
            logging.error(
                f"Beim Erstellen des S3-Clients ist ein Fehler aufgetreten: {e}"
            )
            return None
        return s3

    def list_buckets(self):
        bucket_names = [bucket.name for bucket in self.s3_resource().buckets.all()]
        return bucket_names

    def get_bucket_content(self, bucket_name):
        s3_client = self.s3_client()
        if s3_client is None:
            logging.error("Failed to create S3 client.")
            return []

        try:
            # Call list_objects_v2 method of the s3 client object
            response = s3_client.list_objects_v2(Bucket=bucket_name)
        except Exception as e:
            logging.error(f"An error occurred while listing objects in the bucket: {e}")
            return []

        # Extract 'Contents' from the response
        contents = response.get("Contents", [])
        # Extract 'Key' from each dictionary in the contents
        bucket_content = [obj["Key"] for obj in contents]
        return bucket_content

    def get_s3_extracted_files(self, bucket_name, source_folder):
        try:
            # Call list_objects_v2 method of the s3 client object
            response = self.s3_client().list_objects_v2(
                Bucket=bucket_name, Prefix=source_folder
            )
        except Exception as e:
            self.log_error(f"An error occurred: {e}")
            return []

        # Extract 'Contents' from the response
        contents = response.get("Contents", [])

        # Extract 'Key' from each dictionary in the contents
        bucket_content = [
            (obj["Key"][len(source_folder) :], obj["Size"])
            for obj in contents
            if "/" not in obj["Key"][len(source_folder) :]
        ]
        return bucket_content

    def run(self):
        self.root.mainloop()

    def add_bucket_tabs(self):
        self.folder_icon = PhotoImage(file="folder.png")

        for i, bucket in enumerate(self.list_buckets()):
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=bucket)

            # bucket_content = get_bucket_content(bucket)
            bucket_content = self.get_bucket_content(bucket)
            tree = ttk.Treeview(frame, height=20)  # Set the height of the Treeview
            tree.column("#0", width=400)  # Set the width of the Treeview
            tree.pack(side="left")
            self.listtree = ttk.Treeview(
                frame, columns=("column1", "column2"), show="headings", height=20
            )
            self.listtree.heading("column1", text="Dateiname")
            self.listtree.heading("column2", text="Größe")
            self.listtree.column("column1", width=600)  # Set the width of the Treeview
            self.listtree.pack(side="right")
            id = tree.insert("", "end", text=bucket, open=True, image=self.folder_icon)
            for path in bucket_content:
                current_id = id
                full_path = bucket
                parts = path.split("/")
                for part in parts[:-1]:  # Exclude the last part
                    full_path += "/" + part
                    new_id = None
                    for child_id in tree.get_children(current_id):
                        if tree.item(child_id, "text") == part:
                            new_id = child_id
                            break
                    if new_id is None:
                        new_id = tree.insert(
                            current_id,
                            "end",
                            text=part,
                            values=[full_path, parts[-1]],
                            image=self.folder_icon,
                        )  # Include the last part as a value
                    current_id = new_id

            tree.bind(
                "<<TreeviewSelect>>",
                lambda event, tree=tree, listtree=self.listtree: self.on_tree_select(
                    event, tree, listtree
                ),
            )

    def add_settings_tab(self):
        self.dark_mode_var = BooleanVar()
        self.dark_mode_check = Checkbutton(
            self.settings_frame,
            text="Light Mode",
            variable=self.dark_mode_var,
            command=lambda: self.toggle_dark_mode(),
        )
        self.dark_mode_check.pack()

        self.endpoint_url_entry = self.s3_options(
            self.settings_frame,
            "Endpoint URL",
            50,
            self.config["S3"]["Endpoint URL"],
            False,
        )
        self.access_key_id_entry = self.s3_options(
            self.settings_frame,
            "Access Key ID",
            50,
            self.config["S3"]["Access Key ID"],
            False,
        )
        self.secret_access_key_entry = self.s3_options(
            self.settings_frame,
            "Secret Access Key",
            50,
            self.config["S3"]["Secret Access Key"],
            True,
        )

        save_button = Button(
            self.settings_frame, text="Änderungen speichern", command=self.save_config
        )
        save_button.pack(side="bottom")

    def add_about_tab(self):
        self.about_text = Text(
            self.about_frame, height=20, width=80, font=("Courier", 12), wrap="word"
        )
        self.about_text.pack(side="bottom", expand=True, fill="both")

        self.about_text.insert("end", "S3 Viewer\n\n")
        self.about_text.insert("end", "Version: 0.2\n")
        self.about_text.insert("end", "Author: Benny Fritsch\n")
        self.about_text.insert("end", "License: MIT\n")

        # Center the text
        self.about_text.tag_configure("center", justify="center")
        self.about_text.tag_add("center", "1.0", "end")
        # Disable editing
        self.about_text.configure(state="disabled", bg=self.root.cget("bg"))

    def toggle_dark_mode(self):
        if self.dark_mode_var.get():
            self.root.configure(bg="white")
            self.root.style.theme_use("alt")
        else:
            self.root.configure(bg="black")
            self.root.style.theme_use("dark")

    def on_tree_select(self, event, tree, listtree):
        item = tree.selection()[0]
        listtree.delete(*listtree.get_children())  # Clear the table
        bucket_name, key = tree.item(item, "values")[0].split("/", 1)
        content = self.get_s3_extracted_files(
            bucket_name=bucket_name, source_folder=key + "/"
        )
        for line in content:
            filename, size = line  # Split the tuple into filename and size
            size_kb = size / 1024  # Convert size to kilobytes
            listtree.insert(
                "", "end", values=(filename, str(size_kb.__round__(2)) + " KB")
            )  # Insert the filename and size into the table
        # Bind the row select event
        listtree.bind("<Button-3>", self.on_row_select)

    def on_row_select(self, event):
        # Get selected row
        selected_item = event.widget.selection()

        # Get the 'filename' column value of the selected row
        filename = event.widget.item(selected_item, "values")[0]

        # Open the context menu at the event's x and y coordinates
        print(event.x_root, event.y_root)
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def open_main_window(self):
        self.root.destroy()  # Close the current window
        self.root = Tk()  # Create a new window
        self.root.title("S3 Viewer")
        self.root.geometry("1200x450")
        self.root.style = ttk.Style()
        self.root.style.theme_create(
            "dark",
            parent="alt",
            settings={
                "TNotebook": {
                    "configure": {"tabmargins": [7, 5, 2, 0], "background": "black"}
                },
                "TNotebook.Tab": {
                    "configure": {
                        "padding": [5, 1],
                        "background": "black",
                        "foreground": "white",
                    },
                    "map": {
                        "background": [("selected", "black"), ("active", "grey")],
                        "foreground": [("selected", "white")],
                        "expand": [("selected", [1, 1, 1, 0])],
                    },
                },
                "TFrame": {"configure": {"background": "black"}},
                "TLabel": {"configure": {"background": "black", "foreground": "white"}},
                "TEntry": {
                    "configure": {
                        "fieldbackground": "black",
                        "foreground": "white",
                        "insertbackground": "white",
                    }
                },
                "TCheckbutton": {
                    "configure": {
                        "background": "black",
                        "foreground": "white",
                        "activebackground": "black",
                        "activeforeground": "white",
                    }
                },
                "TButton": {
                    "configure": {
                        "background": "black",
                        "foreground": "white",
                        "activebackground": "black",
                        "activeforeground": "white",
                    }
                },
            },
        )
        self.root.style.theme_use("dark")
        self.notebook = ttk.Notebook(self.root)
        self.settings_frame = ttk.Frame(self.notebook)
        self.about_frame = ttk.Frame(self.notebook)
        self.list_buckets()
        self.add_bucket_tabs()
        self.notebook.add(self.settings_frame, text="Settings")
        self.add_settings_tab()
        self.add_about_tab()
        self.notebook.add(self.about_frame, text="About")
        self.notebook.pack()
        self.root.mainloop()


if not os.path.exists("config.ini"):
    configurator = S3Configurator()
    configurator.run()
else:
    configurator = S3Configurator()
    configurator.open_main_window()
