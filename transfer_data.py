from utils.database import transfer_documents

if __name__ == "__main__":
    num_copied = transfer_documents()
    print(f"Copied {num_copied} documents from source to destination.")