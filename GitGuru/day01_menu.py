while True:
    print("\\n===== GITGURU =====")
    print("1. About GitGuru")
    print("2. Sample questions")
    print("3. Git command rule check")
    print("0. Exit")
    choice = input("Choose: ").strip()

    if choice == "1":
        print("GitGuru helps beginners learn Git and GitHub.")
    elif choice == "2":
        print("What is Git? | How do I clone? | How do I commit? | How do I push?")
    elif choice == "3":
        command = input("Enter git clone, git push, or git pull: ").strip().lower()
        if command == "git clone":
            print("Copies a remote repository to your computer.")
        elif command == "git push":
            print("Uploads local commits to a remote repository.")
        elif command == "git pull":
            print("Fetches and integrates remote changes.")
        else:
            print("Command not covered by this demo.")
    elif choice == "0":
        print("Goodbye from GitGuru!")
        break
    else:
        print("Invalid choice.")
