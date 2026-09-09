import hashlib
import json
from pathlib import Path


# Save the table beside this program, regardless of the terminal's location.
TABLE_FILE = Path(__file__).resolve().with_name("hash_table.json")


def hash_file(filepath):
    """Return the SHA-256 hash of a file's contents."""
    hasher = hashlib.sha256()

    with open(filepath, "rb") as file:
        while True:
            chunk = file.read(4096)
            if not chunk:
                break
            hasher.update(chunk)

    return hasher.hexdigest()


def traverse_directory(directory):
    """Hash files in the directory and its subdirectories."""
    records = []

    for filepath in sorted(directory.rglob("*")):
        # Exclude our output table so it does not try to track itself.
        if filepath.is_file() and filepath.resolve() != TABLE_FILE:
            records.append({
                "filepath": filepath.relative_to(directory).as_posix(),
                "hash": hash_file(filepath)
            })

    return records


def save_table(table):
    with open(TABLE_FILE, "w", encoding="utf-8") as file:
        json.dump(table, file, indent=4)


def generate_table():
    entered_path = input("Enter the directory path to hash: ").strip().strip('"')
    if not entered_path:
        print("Please enter a directory path.")
        return

    directory = Path(entered_path).expanduser().resolve()
    if not directory.is_dir():
        print("That directory does not exist.")
        return

    table = {
        "directory": str(directory),
        "algorithm": "sha256",
        "files": traverse_directory(directory)
    }
    save_table(table)
    print("Hash table generated")
    print(f"Saved to: {TABLE_FILE}")
    print(f"Files recorded: {len(table['files'])}")


def detect_renames(table, stored, current, missing, added):
    """Bonus: infer a rename from a unique unchanged-content match."""
    renamed = False

    for old_path in sorted(missing.copy()):
        old_hash = stored[old_path]
        old_matches = [p for p in missing if stored[p] == old_hash]
        new_matches = [p for p in added if current[p] == old_hash]

        # Avoid guessing when multiple missing/new files have identical data.
        if len(old_matches) == 1 and len(new_matches) == 1:
            new_path = new_matches[0]
            print(f"File name change detected, {old_path} has been renamed to {new_path}")

            for record in table["files"]:
                if record["filepath"] == old_path:
                    record["filepath"] = new_path
                    break

            missing.remove(old_path)
            added.remove(new_path)
            renamed = True

    if renamed:
        save_table(table)
        print("Hash table updated for renamed files.")


def validate_hash():
    if not TABLE_FILE.is_file():
        print("No hash table found. Run option 1 first.")
        return

    with open(TABLE_FILE, "r", encoding="utf-8") as file:
        table = json.load(file)

    directory = Path(table["directory"])
    if not directory.is_dir():
        print(f"The recorded directory is unavailable: {directory}")
        return

    stored = {record["filepath"]: record["hash"] for record in table["files"]}
    current = {record["filepath"]: record["hash"]
               for record in traverse_directory(directory)}

    print(f"Verifying files in: {directory}")

    for filepath in sorted(stored.keys() & current.keys()):
        if stored[filepath] == current[filepath]:
            print(f"{filepath} hash is valid")
        else:
            print(f"{filepath} hash is invalid")

    missing = set(stored) - set(current)
    added = set(current) - set(stored)

    detect_renames(table, stored, current, missing, added)

    for filepath in sorted(missing):
        print(f"{filepath}: file deleted")

    for filepath in sorted(added):
        print(f"{filepath}: new document detected")

    print("Verification complete.")


def main():
    print("1. Generate a new hash table")
    print("2. Verify hashes")
    choice = input("Enter 1 or 2: ").strip()

    try:
        if choice == "1":
            generate_table()
        elif choice == "2":
            validate_hash()
        else:
            print("Invalid option. Run the program again and enter 1 or 2.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Unable to complete the operation: {error}")


if __name__ == "__main__":
    main()
