# Backup the Fakturama database.
import os
import subprocess
import datetime as dt
import argparse
from typing import Optional

TEMPLATE_DATE_PLACEHOLDER_START = "[["
TEMPLATE_DATE_PLACEHOLDER_END = "]]"

type BackupInfo = tuple[dt.date, os.PathLike]

class EmailCredentials:
    def __init__(self, email: str, username: str, password: str):
        """Create a new set of email credentials.

        Args:
            email (str): Email address.
            username (str): Username for the SMTP server.
            password (str): Password for the SMTP server.
        """
        self.email = email
        self.username = username
        self.password = password

class FilenameTemplate:
    """A template for backup files' names.
    """
    def __init__(self, template: str) -> None:
        """Create a new filename template.

        Args:
            template (str): Template string.

        Raises:
            ValueError: Invalid template string.
            ValueError: Invalid date format.
        """
        idx_start = template.find(TEMPLATE_DATE_PLACEHOLDER_START)
        idx_end = template.find(TEMPLATE_DATE_PLACEHOLDER_END)
        if idx_start == -1 or idx_end == -1:
            raise ValueError(f"Date format must be in filename template, enclosed by `{TEMPLATE_DATE_PLACEHOLDER_START}` and `{TEMPLATE_DATE_PLACEHOLDER_END}`")
        
        date_format = template[idx_start + len(TEMPLATE_DATE_PLACEHOLDER_START):idx_end]
        now = dt.date.today()
        if not now.strftime(date_format):
            raise ValueError(f"Invalid date format `{date_format}`")
        
        self._prefix = template[:idx_start]
        self._postfix = template[idx_end + len(TEMPLATE_DATE_PLACEHOLDER_END):]
        self._date_format = date_format
        self._template = template
        
    @property
    def template(self) -> str:
        """
        Returns:
            str: Defining template.
        """
        return self._template
    
    @property
    def prefix(self) -> str:
        """
        Returns:
            str: Template part before the date.
        """
        return self._prefix
    
    @property
    def postfix(self) -> str:
        """
        Returns:
            str: TEmplate part after the date.
        """
        return self._postfix
    
    @property
    def date_format(self) -> str:
        """
        Returns:
            str: Template date format.
        """
        return self._date_format
    
    def match(self, filename: str) -> Optional[dt.date]:
        """Test whether a string matches the template.

        Args:
            filename (str): Filename to test.

        Returns:
            Optional[dt.date]: Filename date according to the template. None if the filename does not match the template.
        """
        if not filename.startswith(self._prefix):
            return None
        if not filename.endswith(self._postfix):
            return None
        
        filename_maybe_date = filename[len(self._prefix):-len(self._postfix)]
        try:
            filename_date = dt.datetime.strptime(filename_maybe_date, self._date_format)
        except ValueError:
            return None
        
        return  filename_date.date()
    
    
def positive_int(value: str) -> int:
    """Ensure a value represents a positive integer.

    Args:
        value (str): Value to check.

    Raises:
        ValueError: Value is not a positive integer.

    Returns:
        int: Integer value.
    """
    value_int = int(value)
    if value_int <= 0:
        raise ValueError("Must be greater than 0")
    
    return value_int


def parse_command_line_arguments() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        argparse.Namespace: Command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="fakturama db backup",
        description="Backup a Faktuama database.",
        epilog="The newest backups are retained.",
    )
    parser.add_argument(
        "-r", "--retain", type=positive_int, default=7, help="Number of backups to retain. The newest backups are retained."
    )
    parser.add_argument(
        "-f",
        "--file",
        type=FilenameTemplate,
        default="faturama.[[%Y%m%d]].bak.sql",
        help=f"Filename template. Date format must be included between `{TEMPLATE_DATE_PLACEHOLDER_START}` and `{TEMPLATE_DATE_PLACEHOLDER_END}` and in replaced by the date the backup is created.",
    )
    parser.add_argument("--dir", type=str, default=".", help="Directory in which to store backups. Can be relative or absolute.")
    parser.add_argument("-n", "--notify", type=str, default=None, help="Email address to send notifications on error.")
    parser.add_argument("-u", "--username", type=str, default=None, help="Email SMTP username.")
    parser.add_argument("-p", "--password", type=str, default=None, help="Email SMTP password.")
    args = parser.parse_args()
    
    if args.notify is not None and (args.username is None or args.password is None):
        parser.error("--notify requires --username and --password")
    
    return args
    
    
def send_error_email(credentials: EmailCredentials, status: subprocess.CompletedProcess):
    """Send an email to the same address as `credentials` indicating an error ocurred while trying to backup the database.

    Args:
        credentials (EmailCredentials): Email credentials to send the mail. The mail is sent to the same address.
        status (subprocess.CompletedProcess): Status of the backup process.
    """
    msg = EmailMessage()
    msg['From'] = credentials.email
    msg['To'] = credentials.email
    msg['Subject'] = "Fakturama backup error"
    msg.set_content(f"The Fakturama backup script encountered an error, returning with code: {status.returncode}.")
    
    with smtplib.SMTP("smtp.uni-stuttgart.de", port=587) as server:
        ssl_context = ssl.create_default_context()
        server.starttls(context=ssl_context)
        server.login(credentials.username, credentials.password)
        server.send_message(msg)

    
def create_backup(template: FilenameTemplate, directory: str | os.PathLike = ".", notify: Optional[EmailCredentials] = None):
    """Create a backup of the database.

    Args:
        template (FilenameTemplate): Template for naming the backup file.
        directory (str | os.PathLike, optional): Directory to place the backup file in. Defaults to ".".
        notify (Optional[EmailCredentials], optional): Email credentials used to send notification in case of error. Defaults to None.
    """
    # TODO
    raise NotImplementedError()
    status = subprocess.run([])
    if status != 0 and notify is not None:
        send_error_email(notify, status)
        

def find_backups(template: FilenameTemplate, directory: str | os.PathLike = ".") -> list[BackupInfo]:
    """Find all backup files in a directory matching `template`.

    Args:
        template (FilenameTemplate): Filename template.
        directory (str | os.PathLike, optional): Directory to search in. Search is not recursive. Defaults to ".".

    Returns:
        list[BackupInfo]: Tuples of (date, path) of matching files. `path` is the absolute path to the file.
    """
    backups = []
    with os.scandir(directory) as it:
        for entry in it:
            if not entry.is_file():
                continue
            
            date = template.match(entry.name)
            if date is None:
                continue
            
            backups.append((date, entry.path))
        
    return backups


def filter_discard_backups(backups: list[BackupInfo], retain: int) -> list[BackupInfo]:
    """Filter backups into those that should be discarded.

    Args:
        backups (list[BackupInfo]): Backups to partition.
        retain (int): Maximum number of backups to retain.

    Returns:
        list[BackupInfo]: Backups to discard.
    """
    backups = sorted(backups, key=lambda backup: backup[0], reverse=True)
    return backups[retain:]

if __name__ == "__main__":
    args = parse_command_line_arguments()
    
    notify = None
    if args.notify is not None:
        import smtplib
        import ssl
        from email.message import EmailMessage
        notify = EmailCredentials(args.notify, args.username, args.password)    
    
    create_backup(args.file, args.dir, notify)
    backups = find_backups(args.file, args.dir)
    discard = filter_discard_backups(backups, args.retain)
    for (_, path) in discard:
        try:
            os.remove(path)
        except Exception:
            pass
    