from app.records import load_records, search, count_by, get_by_id

def start():
    while True:
        print("\\n===== GITGURU KNOWLEDGE BASE =====")
        print("1. Show all  2. Search  3. Count category  4. Find by ID  0. Exit")
        choice = input("Choice: ").strip()
        if choice == "1":
            for r in load_records():
                print(f"\\n[{r['id']}] {r['title']} ({r['category']})")
                print(r["answer"])
        elif choice == "2":
            for r in search(input("Keyword: ")):
                print(f"[{r['id']}] {r['title']}: {r['answer']}")
        elif choice == "3":
            category = input("Category (Git/GitHub): ")
            print(f"{category}: {count_by(category)}")
        elif choice == "4":
            try:
                print(get_by_id(int(input("Record ID: "))) or "Record not found.")
            except ValueError:
                print("Enter a whole-number ID.")
        elif choice == "0":
            print("Goodbye from GitGuru!")
            break
        else:
            print("Invalid choice.")

